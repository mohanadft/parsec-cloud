// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use std::path::PathBuf;

use uuid::Uuid;

use libparsec_tests_lite::prelude::*;

/// A temporary path that will be removed on drop.
pub struct TmpPath(PathBuf);

impl std::ops::Deref for TmpPath {
    type Target = PathBuf;
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl Drop for TmpPath {
    fn drop(&mut self) {
        if let Err(err) = std::fs::remove_dir_all(&self.0) {
            // Cannot remove the directory :'(
            // If we are on Windows, it most likely means a file in the directory
            // is still opened. Typically a SQLite database is still opened because
            // the SQLiteExecutor's drop doesn't wait
            let content = {
                match std::fs::read_dir(&self.0) {
                    Ok(items) => items
                        .into_iter()
                        .map(|item| match item {
                            Ok(item) => {
                                format!("{}", item.path().strip_prefix(&self.0).expect("The item paths are the children of the inner path, they always have it as a prefix").display())
                            }
                            Err(err) => format!("<error: {:?}>", err),
                        })
                        .collect(),
                    Err(_) => vec!["<empty>".to_owned()],
                }
                .join(" ")
            };
            panic!(
                "Cannot remove {:?}: {}\n\
                Content: {}\n\
                Have you done a gracious close of resources in your test ?",
                &self.0, &err, content
            );
        }
    }
}

#[fixture]
pub fn tmp_path() -> TmpPath {
    let mut path = std::env::temp_dir();

    path.extend(["parsec-tests", &Uuid::new_v4().to_string()]);

    std::fs::create_dir_all(&path).expect("Cannot create tmp_path dir");

    TmpPath(path)
}
