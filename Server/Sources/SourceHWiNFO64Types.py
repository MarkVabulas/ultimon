import collections
import struct

# From https://gist.github.com/namazso/0c37be5a53863954c8c8279f66cfb1cc

#	struct HWiNFOHeader
#	{
#	  /* 0x0000 */ uint32_t magic;                   // must be HWiNFO_HEADER_MAGIC
#	  /* 0x0004 */ uint32_t version;                 // 1 as of 6.40-4330
#	  /* 0x0008 */ uint32_t version2;                // 1 as of 6.40-4330
#	  /* 0x000C */ int64_t  last_update;             // unix timestamp
#	  /* 0x0014 */ uint32_t sensor_section_offset;
#	  /* 0x0018 */ uint32_t sensor_element_size;
#	  /* 0x001C */ uint32_t sensor_element_count;
#	  /* 0x0020 */ uint32_t entry_section_offset;
#	  /* 0x0024 */ uint32_t entry_element_size;
#	  /* 0x0028 */ uint32_t entry_element_count;
#	}
#
#	struct HWiNFOSensor
#	{
#	  /* 0x0000 */ uint32_t id;
#	  /* 0x0004 */ uint32_t instance;
#	  /* 0x0008 */ char name_original[128];
#	  /* 0x0088 */ char name_user[128];
#	}
#
#	struct HWiNFOEntry
#	{
#	  /* 0x0000 */ SensorType type;
#	  /* 0x0004 */ uint32_t sensor_index; // !!! not id, this is an index into the other array
#	  /* 0x0008 */ uint32_t id;
#	  /* 0x000C */ char name_original[128];
#	  /* 0x008C */ char name_user[128];
#	  /* 0x010C */ char unit[16];
#	  /* 0x011C */ double value;
#	  /* 0x0124 */ double value_min;
#	  /* 0x012C */ double value_max;
#	  /* 0x0134 */ double value_avg;
#	}

SharedMemoryPath : str = 'Global\\HWiNFO_SENS_SM2'
SharedMemoryMutexPath : str = 'Global\\HWiNFO_SM2_MUTEX'

HWINFO_HEADER_MAGIC = struct.unpack_from('>I', b'SiWH')
HWiNFOHeaderFormat : str = '=IIIqIIIIII'
HWiNFOSensorFormat : str = '=II128s128s'
HWiNFOEntryFormat : str = '=III128s128s16sdddd'

HWiNFOHeaderFormatSize : int = struct.calcsize(HWiNFOHeaderFormat)
HWiNFOSensorFormatSize : int = struct.calcsize(HWiNFOSensorFormat)
HWiNFOEntryFormatSize : int = struct.calcsize(HWiNFOEntryFormat)

HWiNFOHeader = collections.namedtuple('HWiNFOHeader', 'magic version version2 last_update sensor_section_offset sensor_element_size sensor_element_count entry_section_offset entry_element_size entry_element_count')
HWiNFOSensor = collections.namedtuple('HWiNFOSensor', 'id instance name_original name_user')
HWiNFOEntry = collections.namedtuple('HWiNFOEntry', 'type sensor_index id name_original name_user unit value value_min value_max value_avg')
