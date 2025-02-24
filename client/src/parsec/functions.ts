// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

import {
  libparsec,
  InviteListItem,
  WorkspaceInfo,
  RealmRole,
} from '@/plugins/libparsec';

import {
  AvailableDevice,
  ClientConfig,
  DeviceAccessStrategyPassword,
  ClientEvent,
  Handle,
  ClientStartError,
  Result,
  ClientStopError,
  UserInvitation,
  WorkspaceID,
  WorkspaceName,
  InvitationToken,
  InvitationEmailSentStatus,
  NewUserInvitationError,
  ClientListWorkspacesError,
  ClientCreateWorkspaceError,
  InvitationStatus,
  ListInvitationsError,
  NewDeviceInvitationError,
  DeleteInvitationError,
  BootstrapOrganizationError,
  OrganizationID,
  DeviceFileType,
  ParsedBackendAddr,
  BackendAddr,
  ClientEventPing,
  ParseBackendAddrError,
  UserInfo,
  ClientInfoError,
  UserProfile,
  GetWorkspaceNameError,
} from '@/parsec/types';
import { getParsecHandle } from '@/router/conditions';
import { DateTime } from 'luxon';
import { DEFAULT_HANDLE, MOCK_WAITING_TIME, getClientConfig, wait } from '@/parsec/internals';

export async function listAvailableDevices(): Promise<Array<AvailableDevice>> {
  return await libparsec.listAvailableDevices(window.getConfigDir());
}

export async function login(device: AvailableDevice, password: string): Promise<Result<Handle, ClientStartError>> {
  function parsecEventCallback(event: ClientEvent): void {
    console.log('Event received', event);
  }

  if (window.isDesktop()) {
    const clientConfig = getClientConfig();
    const strategy: DeviceAccessStrategyPassword = {
      tag: 'Password',
      password: password,
      keyFile: device.keyFilePath,
    };
    return await libparsec.clientStart(clientConfig, parsecEventCallback, strategy);
  } else {
    return new Promise<Result<Handle, ClientStartError>>((resolve, _reject) => {
      if (password === 'P@ssw0rd.' || password === 'AVeryL0ngP@ssw0rd') {
        resolve({ok: true, value: DEFAULT_HANDLE });
      }
      resolve({ok: false, error: {tag: 'LoadDeviceDecryptionFailed', error: 'WrongPassword'}});
    });
  }
}

export async function logout(): Promise<Result<null, ClientStopError>> {
  const handle = getParsecHandle();

  if (handle !== null && window.isDesktop()) {
    return await libparsec.clientStop(handle);
  } else {
    return new Promise<Result<null, ClientStopError>>((resolve, _reject) => {
      resolve({ok: true, value: null});
    });
  }
}

export async function inviteUser(email: string): Promise<Result<[InvitationToken, InvitationEmailSentStatus], NewUserInvitationError>> {
  const handle = getParsecHandle();

  if (handle !== null && window.isDesktop()) {
    return await libparsec.clientNewUserInvitation(handle, email, true);
  } else {
    return new Promise<Result<[InvitationToken, InvitationEmailSentStatus], NewUserInvitationError>>((resolve, _reject) => {
      resolve({ ok: true, value: ['1234', InvitationEmailSentStatus.Success] });
    });
  }
}

export async function listWorkspaces(): Promise<Result<Array<WorkspaceInfo>, ClientListWorkspacesError>> {
  const handle = getParsecHandle();

  if (handle !== null && window.isDesktop()) {
    return await libparsec.clientListWorkspaces(handle);
  } else {
    return new Promise<Result<Array<WorkspaceInfo>, ClientListWorkspacesError>>((resolve, _reject) => {
      resolve({
        ok: true, value: [
          {'id': '1', 'name': 'Trademeet', 'selfRole': RealmRole.Owner},
          {'id': '2', 'name': 'The Copper Coronet', 'selfRole': RealmRole.Manager},
          {'id': '3', 'name': 'The Asylum', 'selfRole': RealmRole.Contributor},
          {'id': '4', 'name': 'Druid Grove', 'selfRole': RealmRole.Reader},
          // cspell:disable-next-line
          {'id': '5', 'name': 'Menzoberranzan', 'selfRole': RealmRole.Owner},
        ],
      });
    });
  }
}

export async function createWorkspace(name: WorkspaceName): Promise<Result<WorkspaceID, ClientCreateWorkspaceError>> {
  const handle = getParsecHandle();

  if (handle !== null && window.isDesktop()) {
    return await libparsec.clientCreateWorkspace(handle, name);
  } else {
    return new Promise<Result<WorkspaceID, ClientCreateWorkspaceError>>((resolve, _reject) => {
      resolve({ ok: true, value: '1337' });
    });
  }
}

export async function inviteDevice(sendEmail: boolean):
  Promise<Result<[InvitationToken, InvitationEmailSentStatus], NewDeviceInvitationError>> {
  const handle = getParsecHandle();

  if (handle !== null && window.isDesktop()) {
    return await libparsec.clientNewDeviceInvitation(handle, sendEmail);
  }
  return new Promise<Result<[InvitationToken, InvitationEmailSentStatus], NewDeviceInvitationError>>((resolve, _reject) => {
    resolve({ ok: true, value: ['1234', InvitationEmailSentStatus.Success] });
  });
}

export async function listUserInvitations(): Promise<Result<Array<UserInvitation>, ListInvitationsError>> {
  const handle = getParsecHandle();

  if (handle !== null && window.isDesktop()) {
    const result = await libparsec.clientListInvitations(handle);

    if (!result.ok) {
      return result;
    }
    // No need to add device invitations
    result.value = result.value.filter((item: InviteListItem) => item.tag === 'User');
    // Convert InviteListItemUser to UserInvitation
    result.value = result.value.map((item) => {
      // @ts-expect-error: Actual f64 to Luxon's Datetime conversion
      (item as UserInvitation).date = DateTime.fromSeconds(item.createdOn);
      return item;
    });
    return result as any;
  } else {
    return new Promise<Result<Array<UserInvitation>, ListInvitationsError>>((resolve, _reject) => {
      const ret: Array<UserInvitation> = [{
        tag: 'User',
        token: '1234',
        createdOn: DateTime.now(),
        claimerEmail: 'shadowheart@swordcoast.faerun',
        status: InvitationStatus.Ready,
        date: DateTime.now(),
      }, {
        tag: 'User',
        token: '5678',
        createdOn: DateTime.now(),
        claimerEmail: 'gale@waterdeep.faerun',
        status: InvitationStatus.Ready,
        date: DateTime.now(),
      }];
      resolve({ ok: true, value: ret });
    });
  }
}

export async function cancelInvitation(token: InvitationToken): Promise<Result<null, DeleteInvitationError>> {
  const handle = getParsecHandle();

  if (handle !== null && window.isDesktop()) {
    return await libparsec.clientDeleteInvitation(handle, token);
  } else {
    return new Promise<Result<null, DeleteInvitationError>>((resolve, _reject) => {
      resolve({ok: true, value: null});
    });
  }
}

export async function createOrganization(
  backendAddr: BackendAddr, orgName: OrganizationID, userName: string, email: string, password: string, deviceLabel: string,
): Promise<Result<AvailableDevice, BootstrapOrganizationError>> {
  function parsecEventCallback(event: ClientEventPing): void {
    console.log('On event', event);
  }

  const bootstrapAddr = await libparsec.buildBackendOrganizationBootstrapAddr(backendAddr, orgName);

  if (window.isDesktop()) {
    const config: ClientConfig = {
      configDir: window.getConfigDir(),
      dataBaseDir: window.getDataBaseDir(),
      mountpointBaseDir: window.getMountpointDir(),
      workspaceStorageCacheSize: {tag: 'Default'},
    };
    return await libparsec.bootstrapOrganization(
      config,
      parsecEventCallback,
      bootstrapAddr,
      {tag: 'Password', password: password},
      {label: userName, email: email},
      deviceLabel,
      null,
    );
  } else {
    await wait(MOCK_WAITING_TIME);
    return new Promise<Result<AvailableDevice, BootstrapOrganizationError>>((resolve, _reject) => {
      resolve({ok: true, value: {
        keyFilePath: '/path',
        organizationId: 'MyOrg',
        deviceId: 'deviceid',
        humanHandle: {
          label: 'A',
          email: 'a@b.c',
        },
        deviceLabel: 'a@b',
        slug: 'slug',
        ty: DeviceFileType.Password,
      }});
    });
  }
}

export async function parseBackendAddr(addr: string): Promise<Result<ParsedBackendAddr, ParseBackendAddrError>> {
  return await libparsec.parseBackendAddr(addr);
}

export async function getUserInfo(): Promise<Result<UserInfo, ClientInfoError>> {
  const handle = getParsecHandle();

  if (handle !== null && window.isDesktop()) {
    return await libparsec.clientInfo(handle);
  } else {
    return new Promise<Result<UserInfo, ClientInfoError>>((resolve, _reject) => {
      resolve({ok: true, value: {
        organizationId: 'MyOrg',
        deviceId: 'a@b',
        deviceLabel: 'My Device',
        userId: 'userid',
        currentProfile: UserProfile.Admin,
        humanHandle: {
          email: 'user@host.com',
          label: 'Gordon Freeman',
        },
      }});
    });
  }
}

export async function getUserProfile(): Promise<UserProfile | null> {
  const result = await getUserInfo();

  if (result.ok) {
    return result.value.currentProfile;
  } else {
    return null;
  }
}

export async function isAdmin(): Promise<boolean> {
  return await getUserProfile() === UserProfile.Admin;
}

export async function isOutsider(): Promise<boolean> {
  return await getUserProfile() === UserProfile.Outsider;
}

export async function getWorkspaceName(workspaceId: WorkspaceID): Promise<Result<WorkspaceName, GetWorkspaceNameError>> {
  const handle = getParsecHandle();

  if (handle !== null && window.isDesktop()) {
    const result = await libparsec.clientListWorkspaces(handle);
    if (result.ok) {
      const workspace = result.value.find((info) => {
        if (info.id === workspaceId) {
          return true;
        }
        return false;
      });
      if (workspace) {
        return new Promise<Result<WorkspaceName, GetWorkspaceNameError>>((resolve, _reject) => {
          resolve({ok: true, value: workspace.name});
        });
      }
    }
    return new Promise<Result<WorkspaceID, GetWorkspaceNameError>>((resolve, _reject) => {
      resolve({ok: false, error: {tag: 'NotFound'}});
    });
  } else {
    return new Promise<Result<WorkspaceID, GetWorkspaceNameError>>((resolve, _reject) => {
      resolve({ok: true, value: 'My Workspace'});
    });
  }
}

export async function isValidWorkspaceName(name: string): Promise<boolean> {
  return await libparsec.validateEntryName(name);
}

export async function isValidPath(path: string): Promise<boolean> {
  return await libparsec.validatePath(path);
}

export async function isValidUserName(name: string): Promise<boolean> {
  return await libparsec.validateHumanHandleLabel(name);
}

export async function isValidEmail(email: string): Promise<boolean> {
  return await libparsec.validateEmail(email);
}

export async function isValidDeviceName(name: string): Promise<boolean> {
  return await libparsec.validateDeviceLabel(name);
}

export async function isValidInvitationToken(token: string): Promise<boolean> {
  return await libparsec.validateInvitationToken(token);
}
