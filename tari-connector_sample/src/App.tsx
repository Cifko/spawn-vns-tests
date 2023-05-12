import { TariConnection, TariConnectorButton } from "tari-connector/src/index";
import "./App.css";
import { ResourceAddress, Hash, TariPermissions, TariPermissionAccountBalance, SubstateAddress, NonFungibleAddress, NonFungibleAddressContents, NonFungibleId, U256, TariPermissionTransactionSend } from "tari-connector/src/tari_permissions";
import { useState } from 'react';

function App() {
  const [tari, setTari] = useState<TariConnection | undefined>();

  const onOpen = (tari: TariConnection) => {
    setTari(tari);
    window.tari = tari;
  }
  let address = import.meta.env.VITE_SIGNALING_SERVER_ADDRESS || "http://localhost:9100";
  const setAnswer = () => {
    tari?.setAnswer();
  }
  let permissions = new TariPermissions();
  // permissions.addPermission(new TariPermissionAccountList(new ComponentAddress(new Hash([1, 2, 3]))))
  permissions.addPermission(new TariPermissionTransactionSend(new SubstateAddress(new ResourceAddress(new Hash([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31])))))
  let optional_permissions = new TariPermissions();
  optional_permissions.addPermission(new TariPermissionAccountBalance(new SubstateAddress(new NonFungibleAddress(new NonFungibleAddressContents(
    new ResourceAddress(new Hash([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31])),
    new NonFungibleId(new U256([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31])),
  )))))
  return (
    <>
      <TariConnectorButton signalingServer={address} permissions={permissions} optional_permissions={optional_permissions} onOpen={onOpen} />
      {tari ? <button onClick={setAnswer}>SetAnswer</button> : null}
    </>
  );
}

export default App;
