// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

mod entry_transactions;
mod fetch;

pub use entry_transactions::*;

use std::{
    ops::DerefMut,
    sync::{Arc, Mutex},
};

use libparsec_client_connection::AuthenticatedCmds;
use libparsec_platform_storage::workspace::{WorkspaceCacheStorage, WorkspaceDataStorage};
use libparsec_types::prelude::*;

use crate::{certificates_ops::CertificatesOps, event_bus::EventBus, ClientConfig};

#[derive(Debug)]
pub(crate) struct UserDependantConfig {
    pub realm_key: SecretKey,
    pub user_role: RealmRole,
    pub workspace_name: EntryName,
}

#[derive(Debug)]
pub struct WorkspaceOps {
    #[allow(unused)]
    config: Arc<ClientConfig>,
    #[allow(unused)]
    device: Arc<LocalDevice>,
    data_storage: WorkspaceDataStorage,
    cache_storage: WorkspaceCacheStorage,
    #[allow(unused)]
    cmds: Arc<AuthenticatedCmds>,
    #[allow(unused)]
    certificates_ops: Arc<CertificatesOps>,
    #[allow(unused)]
    event_bus: EventBus,
    realm_id: VlobID,
    user_dependant_config: Mutex<UserDependantConfig>,
}

#[derive(Debug, thiserror::Error)]
pub enum WorkspaceOpsError {
    #[error("Unknown workspace `{0}`")]
    UnknownWorkspace(VlobID),
    #[error(transparent)]
    Internal(#[from] anyhow::Error),
}

#[derive(Debug)]
pub struct ReencryptionJob {}

// For readability, we define the public interface here and let the actual
// implementation in separated submodules
impl WorkspaceOps {
    /*
     * Crate-only interface (used by client, opses and monitors)
     */

    pub(crate) async fn start(
        config: Arc<ClientConfig>,
        device: Arc<LocalDevice>,
        cmds: Arc<AuthenticatedCmds>,
        certificates_ops: Arc<CertificatesOps>,
        event_bus: EventBus,
        realm_id: VlobID,
        user_dependant_config: UserDependantConfig,
    ) -> Result<Self, anyhow::Error> {
        // TODO: handle errors
        let data_storage =
            WorkspaceDataStorage::start(&config.data_base_dir, device.clone(), realm_id).await?;
        let cache_storage = WorkspaceCacheStorage::start(
            &config.data_base_dir,
            config.workspace_storage_cache_size.cache_size(),
            device.clone(),
            realm_id,
        )
        .await?;
        Ok(Self {
            config,
            device,
            data_storage,
            cache_storage,
            cmds,
            certificates_ops,
            event_bus,
            realm_id,
            user_dependant_config: Mutex::new(user_dependant_config),
        })
    }

    /// Stop the underlying storage (and flush whatever data is not yet on disk)
    ///
    /// Once stopped, it can still theoretically be used (i.e. `stop` doesn't
    /// consume `self`), but will do nothing but return stopped error.
    pub(crate) async fn stop(&self) -> anyhow::Result<()> {
        // TODO: is the storages teardown order important ?
        self.data_storage
            .stop()
            .await
            .context("Cannot stop data storage")?;
        self.cache_storage.stop().await;
        Ok(())
    }

    pub(crate) fn update_user_dependant_config(
        &self,
        updater: impl FnOnce(&mut UserDependantConfig),
    ) {
        let mut guard = self
            .user_dependant_config
            .lock()
            .expect("Mutex is poisoned");
        updater(guard.deref_mut());
    }

    /*
     * Public interface
     */

    pub fn realm_id(&self) -> VlobID {
        self.realm_id
    }

    pub async fn entry_info(&self, path: &FsPath) -> Result<EntryInfo, EntryInfoError> {
        entry_transactions::entry_info(self, path).await
    }
}

#[cfg(test)]
#[path = "../../tests/unit/workspace_ops/mod.rs"]
#[allow(clippy::unwrap_used)]
mod tests;
