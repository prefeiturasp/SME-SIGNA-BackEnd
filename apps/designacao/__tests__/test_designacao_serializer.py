from django.test import TestCase
from apps.designacao.api.serializers.designacao_serializer import DesignacaoSerializer

class DesignacaoSerializerTest(TestCase):
    def test_get_field_names_inclui_campos_extras(self):
        serializer = DesignacaoSerializer()
        fields = serializer.fields

        self.assertIn('impedimento_substituicao_detail', fields)
        self.assertIn('tipo_vaga_display', fields)
        self.assertIn('cargo_vaga_display', fields)