import unittest
import main
#import exceptions

class MainTestCase(unittest.TestCase):
    #tests for the main.py

    #packageName
    def testPackageNameGivenAValidFile(self):
        self.assertEquals(main.packageName('../scripts/button.apk'),'com.test.bbutton')

    def test_packageName_given_bad_filename(self):
        self.assertRaises(OSError,main.packageName,'test')
        
    def testPacakgeName_given_non_string(self):
        self.assertRaises(AttributeError,main.packageName,12)

    def test_runProcess_given_valid_command(self):
        self.assertEquals(main.runProcess('echo hello world'),None)
    def test_runProcess_given_bad_arg(self):
        self.assertRaises(AttributeError,main.runProcess,12)

    def test_runProcess_given_bad_command(self):
        self.assertRaises(RuntimeError,main.runProcess,'test')

if __name__ == '__main__':
    unittest.main()
