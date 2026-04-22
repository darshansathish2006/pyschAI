from django.db import models
from django.contrib.auth.models import User

# class SurveyResult(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     score = models.IntegerField()
#     level = models.CharField(max_length=50)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.user.username} - {self.level}"

class Assessment(models.Model):
    TEST_CHOICES = [
        ('PHQ9', 'PHQ-9'),
        ('BDI', 'BDI'),
    ]

    user=models.ForeignKey(User,on_delete=models.CASCADE)

    test_type=models.CharField(max_length=10,choices=TEST_CHOICES)
    responses=models.JSONField()

    total_score=models.IntegerField()

    severity = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.test_type} - {self.total_score}"