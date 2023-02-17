// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS

//! Send Authenticated commands to the server.
//!
//! The HTTP-request will contain the following headers for authentication:
//!
//! ```text
//! Authorization: PARSEC-SIGN-ED25519
//! Author: [base64 string]
//! Timestamp: [DateTime UTC RFC3339 with millisecond]
//! Signature: [base64 ed25519 signature]
//! ```
//! The signature is generated by appending the following data:
//!
//! 1. `author` (in base64, contains in header `Author`)
//! 2. `timestamp` (date time UTC RFC3339 with millisecond, contains in header `Timestamp`)
//! 3. `body` (the http body in bytes)
//!
//! # Why using rfc 3339 instead of rfc 2822 ?
//!
//! > Because I can, that's why
//! > @me
//!
//! The reasons are listed [here](https://datatracker.ietf.org/doc/html/rfc3339#section-5)
//!
//! 1. Ordering
//! 2. Tradeoff between human readability and interoperability
//! 3. Redundant information (i.e.: we don't need the day of week)
//!
//! Beside the headers for authentication, we also add the header `API_VERSION` that contain the [parsec_api_protocol::ApiVersion]
//!

use base64::prelude::{Engine, BASE64_STANDARD};
use libparsec_crypto::SigningKey;
use libparsec_protocol::{ApiVersion, Request};
use libparsec_types::{BackendOrganizationAddr, DeviceID};
use reqwest::{
    header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_LENGTH, CONTENT_TYPE},
    Client, RequestBuilder, Url,
};

use crate::error::{CommandError, CommandResult};

/// Method name that will be used for the header `Authorization` to indicate that will be using this method.
pub const PARSEC_AUTH_METHOD: &str = "PARSEC-SIGN-ED25519";
/// How we serialize the data before sending a request.
pub const PARSEC_CONTENT_TYPE: &str = "application/msgpack";

pub const API_VERSION_HEADER_NAME: &str = "Api-Version";

/// Factory that send commands in a authenticated context.
pub struct AuthenticatedCmds {
    /// HTTP Client that contain the basic configuration to communicate with the server.
    client: Client,
    addr: BackendOrganizationAddr,
    url: Url,
    device_id: String,
    signing_key: SigningKey,
}

impl AuthenticatedCmds {
    /// Create a new `AuthenticatedCmds`
    pub fn new(
        client: Client,
        addr: BackendOrganizationAddr,
        device_id: DeviceID,
        signing_key: SigningKey,
    ) -> Result<Self, url::ParseError> {
        let url = addr.to_authenticated_http_url();

        let device_id = BASE64_STANDARD.encode(device_id.to_string().as_bytes());

        Ok(Self {
            client,
            addr,
            url,
            device_id,
            signing_key,
        })
    }

    pub fn addr(&self) -> &BackendOrganizationAddr {
        &self.addr
    }
}

/// Prepare a new request, the body will be added to the Request using [RequestBuilder::body]
fn prepare_request(
    request_builder: RequestBuilder,
    signing_key: &SigningKey,
    device_id: &str,
    body: Vec<u8>,
) -> RequestBuilder {
    let request_builder = sign_request(request_builder, signing_key, device_id, &body);

    let mut content_headers = HeaderMap::with_capacity(2);
    content_headers.insert(
        API_VERSION_HEADER_NAME,
        HeaderValue::from_str(&libparsec_protocol::API_VERSION.to_string())
            .expect("api version must contains valid char"),
    );
    content_headers.insert(CONTENT_TYPE, HeaderValue::from_static(PARSEC_CONTENT_TYPE));
    content_headers.insert(
        CONTENT_LENGTH,
        HeaderValue::from_str(&body.len().to_string()).expect("numeric value are valid char"),
    );

    request_builder.headers(content_headers).body(body)
}

/// Sing a request by adding specific headers.
fn sign_request(
    request_builder: RequestBuilder,
    signing_key: &SigningKey,
    device_id: &str,
    body: &[u8],
) -> RequestBuilder {
    let timestamp = chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Millis, true);
    let signature = signing_key.sign_only_signature(body);
    let signature = BASE64_STANDARD.encode(signature);

    let mut authorization_headers = HeaderMap::with_capacity(4);

    authorization_headers.insert(AUTHORIZATION, HeaderValue::from_static(PARSEC_AUTH_METHOD));
    authorization_headers.insert(
        "Author",
        HeaderValue::from_str(device_id).expect("base64 shouldn't contain invalid char"),
    );
    authorization_headers.insert(
        "Timestamp",
        HeaderValue::from_str(&timestamp)
            .expect("should contain only numeric char which are valid char"),
    );
    authorization_headers.insert(
        "Signature",
        HeaderValue::from_str(&signature).expect("base64 shouldn't contain invalid char"),
    );

    request_builder.headers(authorization_headers)
}

impl AuthenticatedCmds {
    pub async fn send<T>(
        &self,
        request: T,
    ) -> CommandResult<<T as libparsec_protocol::Request>::Response>
    where
        T: Request,
    {
        let request_builder = self.client.post(self.url.clone());

        let data = request.dump()?;

        let req = prepare_request(request_builder, &self.signing_key, &self.device_id, data).send();
        let resp = req.await?;
        match resp.status().as_u16() {
            200 => {
                let response_body = resp.bytes().await?;
                Ok(T::load_response(&response_body)?)
            }
            415 => Err(CommandError::BadContent),
            422 => {
                let headers = resp.headers();

                let api_version = headers
                    .get("Api-Version")
                    .ok_or(CommandError::MissingApiVersion)?
                    .to_str()
                    .unwrap_or_default();
                let api_version = api_version
                    .try_into()
                    .map_err(|_| CommandError::WrongApiVersion(api_version.into()))?;

                let supported_api_versions = resp
                    .headers()
                    .get("Supported-Api-Versions")
                    .ok_or(CommandError::MissingSupportedApiVersions)?
                    .to_str()
                    .unwrap_or_default()
                    .split(';')
                    .filter_map(|x| ApiVersion::try_from(x).ok())
                    .collect();

                Err(CommandError::UnsupportedApiVersion {
                    api_version,
                    supported_api_versions,
                })
            }
            460 => Err(CommandError::ExpiredOrganization),
            461 => Err(CommandError::RevokedUser),
            _ => Err(CommandError::InvalidResponseStatus(resp.status(), resp)),
        }
    }
}
