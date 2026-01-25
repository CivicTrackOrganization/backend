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

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

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
    image = models.ImageField(upload_to='reports/', null=True, blank=True)
    location = models.CharField(max_length=200, db_default='')
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
    report = models.ForeignKey(to=Report, on_delete=models.CASCADE, related_name="statuses")
    
    STATUS_CHOICES = [
        (status.value, status.name)
        for status in ReportStatusEnum
    ]

    status_name = models.CharField(max_length=11, choices=STATUS_CHOICES)
    moderator_comment = models.TextField(blank=True, null=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class Vote(models.Model):
    VOTE_CHOICES = [
        (1, 'Upvote'),
        (-1, 'Downvote')
    ]
    
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='votes')
    vote_type = models.SmallIntegerField(choices=VOTE_CHOICES)
    created_at = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('report', 'created_by')

class Comment(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    is_official_response = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)