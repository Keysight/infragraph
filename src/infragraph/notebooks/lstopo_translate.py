#%%
import os
from infragraph.translators.lstopo_translator import LstopoParser
from infragraph import *

#%% 
current_dir = os.path.dirname(os.path.abspath(__file__))
mock_data_path = os.path.join(current_dir, "../../tests/test_translators/resources")
lstopo_xml_file = os.path.join(mock_data_path, "supermicro.xml")

#%%
lstopo_parser = LstopoParser(lstopo_xml_file)
infra_obj = lstopo_parser.parse()

