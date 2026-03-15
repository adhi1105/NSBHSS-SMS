from django.test import SimpleTestCase
from django.urls import reverse

class BulkWhatsAppRoutingTests(SimpleTestCase):
    def test_view_url_exists(self):
        url = reverse('communication:bulk_whatsapp')
        self.assertEqual(url, '/communication/whatsapp/')

    def test_api_url_exists(self):
        url = reverse('communication:api_filter_users')
        self.assertEqual(url, '/communication/whatsapp/api/fetch-recipients/')
        
    def test_settings_url_exists(self):
        url = reverse('communication:api_settings')
        self.assertEqual(url, '/communication/whatsapp/settings/')
