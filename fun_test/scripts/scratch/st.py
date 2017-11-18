from lib.host.storage_controller import StorageController
import uuid

st = StorageController(target_ip="10.1.20.67", target_port=40220)
st.ip_cfg(ip="10.1.20.67")
this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
result = st.create_blt_volume(capacity=1073741824,
                                              block_size=4096,
                                              name="volume1",
                                              uuid=this_uuid)
print result