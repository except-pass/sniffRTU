import unittest 
from sniffRTU.parsehex import ReadRequest, ReadResponse

class TestParse(unittest.TestCase):
    def test_readrequest_fc3(self):
        request_hexl = ['11','03','00','6B','00', '03', '76', '87']
        rr = ReadRequest.from_hex(request_hexl)
        self.assertEqual(rr.slaveid, 17) #\x11
        self.assertEqual(rr.fc, 3)
        self.assertEqual(rr.address, 107) #\x006B
        self.assertEqual(rr.num_registers, 3)
        self.assertEqual(rr.raw, '1103006B00037687')
        self.assertTrue(rr.check_crc())

    def test_readresp_fc3(self):
        response_hexs = '110306AE415652434049AD--- a bunch of garbage at the end'
        rr = ReadResponse.from_raw(response_hexs)
        self.assertEqual(rr.slaveid, 17) #\x11
        self.assertEqual(rr.fc, 3)
        self.assertEqual(rr.num_bytes, 6)
        self.assertListEqual(rr.payload, ['AE', '41', '56', '52', '43', '40'])
        self.assertEqual(rr.total_length, 11)
        self.assertTrue(rr.check_crc())
        self.assertEqual(rr.raw, '110306AE415652434049AD')

if __name__ == '__main__':
    unittest.main()