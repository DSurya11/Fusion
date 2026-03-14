from django.test import SimpleTestCase

from applications.hr2 import selectors, services


class RegistrySmokeTest(SimpleTestCase):
    def test_form_model_registry_contains_all_expected_forms(self):
        expected = {"LTC", "CPDAAdvance", "CPDAReimbursement", "Leave", "Appraisal"}
        self.assertEqual(set(selectors.FORM_MODEL_REGISTRY.keys()), expected)

    def test_form_type_filetracking_contains_all_expected_forms(self):
        expected = {"LTC", "CPDAAdvance", "CPDAReimbursement", "Leave", "Appraisal"}
        self.assertEqual(set(services.FORM_TYPE_FILETRACKING.keys()), expected)
