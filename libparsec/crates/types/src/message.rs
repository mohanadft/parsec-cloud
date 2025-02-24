// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use std::io::{Read, Write};

use flate2::read::ZlibDecoder;
use flate2::write::ZlibEncoder;
use serde::{Deserialize, Serialize};
use serde_with::serde_as;

use libparsec_crypto::{PrivateKey, PublicKey, SecretKey, SigningKey, VerifyKey};

use crate::{DataError, DateTime, DeviceID, EntryName, IndexInt, VlobID};

#[serde_as]
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(tag = "type")]
pub enum MessageContent {
    #[serde(rename = "sharing.granted")]
    SharingGranted {
        author: DeviceID,
        timestamp: DateTime,

        name: EntryName,
        id: VlobID,
        encryption_revision: IndexInt,
        encrypted_on: DateTime,
        key: SecretKey,
        // Don't include role given the only reliable way to get this information
        // is to fetch the realm role certificate from the backend.
        // Besides, we will also need the message sender's realm role certificate
        // to make sure he is an owner.
    },

    #[serde(rename = "sharing.reencrypted")]
    SharingReencrypted {
        author: DeviceID,
        timestamp: DateTime,

        // This message is similar to `sharing.granted`. Hence both can be processed
        // interchangeably, which avoid possible concurrency issues when a sharing
        // occurs right before a reencryption.
        name: EntryName,
        id: VlobID,
        encryption_revision: IndexInt,
        encrypted_on: DateTime,
        key: SecretKey,
    },

    #[serde(rename = "sharing.revoked")]
    SharingRevoked {
        author: DeviceID,
        timestamp: DateTime,

        id: VlobID,
    },

    #[serde(rename = "ping")]
    Ping {
        author: DeviceID,
        timestamp: DateTime,

        ping: String,
    },
}

impl MessageContent {
    pub fn verify_and_load_for(
        signed: &[u8],
        author_verify_key: &VerifyKey,
        expected_author: &DeviceID,
        expected_timestamp: DateTime,
    ) -> Result<MessageContent, DataError> {
        let compressed = author_verify_key
            .verify(signed)
            .map_err(|_| DataError::Signature)?;
        let mut serialized = vec![];
        ZlibDecoder::new(compressed)
            .read_to_end(&mut serialized)
            .map_err(|_| DataError::Compression)?;
        let data: MessageContent =
            rmp_serde::from_slice(&serialized).map_err(|_| DataError::Serialization)?;
        let (author, &timestamp) = match &data {
            MessageContent::SharingGranted {
                author, timestamp, ..
            } => (author, timestamp),
            MessageContent::SharingReencrypted {
                author, timestamp, ..
            } => (author, timestamp),
            MessageContent::SharingRevoked {
                author, timestamp, ..
            } => (author, timestamp),
            MessageContent::Ping {
                author, timestamp, ..
            } => (author, timestamp),
        };
        if author != expected_author {
            Err(DataError::UnexpectedAuthor {
                expected: Box::new(expected_author.clone()),
                got: Some(Box::new(author.clone())),
            })
        } else if timestamp != expected_timestamp {
            Err(DataError::UnexpectedTimestamp {
                expected: expected_timestamp,
                got: timestamp,
            })
        } else {
            Ok(data)
        }
    }

    pub fn decrypt_verify_and_load_for(
        ciphered: &[u8],
        recipient_privkey: &PrivateKey,
        author_verify_key: &VerifyKey,
        expected_author: &DeviceID,
        expected_timestamp: DateTime,
    ) -> Result<MessageContent, DataError> {
        let signed = recipient_privkey
            .decrypt_from_self(ciphered)
            .map_err(|_| DataError::Decryption)?;
        Self::verify_and_load_for(
            &signed,
            author_verify_key,
            expected_author,
            expected_timestamp,
        )
    }

    pub fn dump_and_sign(&self, author_signkey: &SigningKey) -> Vec<u8> {
        let serialized =
            rmp_serde::to_vec_named(&self).expect("MessageContent should be serializable");
        let mut e = ZlibEncoder::new(Vec::new(), flate2::Compression::default());
        let compressed = e
            .write_all(&serialized)
            .and_then(|_| e.finish())
            .expect("in-memory buffer should not fail");
        author_signkey.sign(&compressed)
    }

    pub fn dump_sign_and_encrypt_for(
        &self,
        author_signkey: &SigningKey,
        recipient_pubkey: &PublicKey,
    ) -> Vec<u8> {
        let signed = self.dump_and_sign(author_signkey);
        recipient_pubkey.encrypt_for_self(&signed)
    }
}
