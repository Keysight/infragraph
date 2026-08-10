#%%
import os
import json
import yaml
from infragraph.translators.nccl_translator import NcclParser
from infragraph import *

#%%
current_dir = os.path.dirname(os.path.abspath(__file__))
mock_data_path = os.path.join(current_dir, "../../tests/test_translators/resources")
nccl_xml_file = os.path.join(mock_data_path, "dgx_a100_nccl_topo.xml")

#%%
nccl_parser = NcclParser(nccl_xml_file, device_name="dgx_a100")
infra_obj = nccl_parser.parse()
print(infra_obj)

#%%


# Build the annotated graph (infrastructure + annotations) and print it as YAML.
service = nccl_parser.get_annotations()
req = GraphRequest()
req.infragraph.annotations.choice = "full"
annotated_graph = service.get_graph(req)  # returns a JSON string
# %%
