from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

from api.choices import AssignedUnit, ReportPriority, ReportStatusEnum, ReportType

class UserRole(models.TextChoices):
    CITIZEN = "citizen", "Citizen"
    MODERATOR = "moderator", "Moderator"

class User(AbstractUser):
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("first_name", "last_name", "username")

    def __str__(self) -> str:
        return self.email
    
    role = models.CharField(
        max_length=20, 
        choices=UserRole.choices, 
        default=UserRole.CITIZEN
    )

class Report(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    longitude = models.FloatField(
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
        db_default=0.0
    )
    latitude = models.FloatField(
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
        db_default=0.0
    )
    
    PRIORITY_CHOICES = [
        (priority.value, priority.name)
        for priority in ReportPriority
    ]
    
    priority = models.CharField(max_length=6, choices=PRIORITY_CHOICES)

    TYPE_CHOICES = [
        (report_type.value, report_type.name)
        for report_type in ReportType
    ]

    type = models.CharField(max_length=14, choices=TYPE_CHOICES)

    ASSIGNED_UNIT_CHOICES = [
        (assigned_unit.value, assigned_unit.name)
        for assigned_unit in AssignedUnit
    ]

    assigned_unit = models.CharField(
        max_length=13,
        choices=ASSIGNED_UNIT_CHOICES
    )
    created_at = models.DateField(auto_now_add=True)

class ReportStatus(models.Model):
    report = models.OneToOneField(to=Report, on_delete=models.CASCADE, related_name="status")
    
    STATUS_CHOICES = [
        (status.value, status.name)
        for status in ReportStatusEnum
    ]

    status_name = models.CharField(max_length=11, choices=STATUS_CHOICES)
    moderator_comment = models.TextField(blank=True, null=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    modified_at = models.DateField(auto_now=True)