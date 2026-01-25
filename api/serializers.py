from .models import Report, User
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.validators import MinValueValidator, MaxValueValidator
from api.choices import ReportStatusEnum, AssignedUnit

class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name")
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"]
        )
        return user

class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role"]
        read_only_fields = ["id", "role"]

class ReportSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    moderator_comment = serializers.SerializerMethodField()
    coordinates = serializers.ListField(
        child=serializers.FloatField(),
        write_only=True,
        min_length=2,
        max_length=2,
        required=True,
        allow_null=False,
        help_text="Format: [longitude, latitude]"
    )

    class Meta:
        model = Report
        fields = [
            'id', 'title', 'description', 'longitude', 'latitude', 'coordinates',
            'priority', 'type', 'status', 'moderator_comment', 'author', 'assigned_unit', 'created_at'
        ]
        read_only_fields = ['longitude', 'latitude', 'status', 'moderator_comment', 'author', 'assigned_unit', 'created_at']

    def get_author(self, obj):
        if obj.author:
            return f"{obj.author.first_name} {obj.author.last_name}".strip()
        return ""
    
    def get_status(self, obj):
        if obj.status:
            return obj.status.status_name
        return ""
    
    def get_moderator_comment(self, obj):
        if hasattr(obj, 'status') and obj.status:
            return obj.status.moderator_comment
        return ""

    def create(self, validated_data):
        coords = validated_data.pop('coordinates')
        validated_data['longitude'] = coords[0]
        validated_data['latitude'] = coords[1]
        return super().create(validated_data)

    def validate_coordinates(self, value):
        if not value or len(value) != 2:
            raise serializers.ValidationError("Coordinates must be a list of exactly 2 numbers [longitude, latitude].")
        
        longitude, latitude = value
        
        try:
            longitude = float(longitude)
            latitude = float(latitude)
        except (TypeError, ValueError):
            raise serializers.ValidationError("Coordinates must be numeric values.")
        
        if not (-180 <= longitude <= 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        if not (-90 <= latitude <= 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        
        return value

class ChangeStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[s.value for s in ReportStatusEnum])
    comment = serializers.CharField(required=False, allow_blank=True)
    assigned_unit = serializers.ChoiceField(choices=[u.value for u in AssignedUnit], required=False)