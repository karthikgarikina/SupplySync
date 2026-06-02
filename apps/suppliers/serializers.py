from rest_framework import serializers


class SupplierSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    supplier_code = serializers.CharField(required=False, allow_blank=False, max_length=20)
    name = serializers.CharField(required=True, allow_blank=False, max_length=200)
    contact_person = serializers.CharField(required=True, allow_blank=False, max_length=150)
    email = serializers.EmailField(required=True, allow_blank=False)
    phone = serializers.CharField(required=True, allow_blank=False, max_length=20)
    address = serializers.CharField(required=True, allow_blank=False)
    city = serializers.CharField(required=True, allow_blank=False, max_length=100)
    state = serializers.CharField(required=True, allow_blank=False, max_length=100)
    pincode = serializers.CharField(required=True, allow_blank=False, max_length=10)
    gstin = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=20)
    is_active = serializers.BooleanField(required=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

