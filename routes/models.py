from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class MountainRange(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class StartingPoint(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Gear(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Route(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Легкий'),
        ('medium', 'Середній'),
        ('hard', 'Складний'),
    ]

    DURATION_CHOICES = [
        ('one_day', 'Одноденний'),
        ('overnight', 'З ночівлею'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()

    distance_km = models.FloatField(validators=[MinValueValidator(0.0)])
    elevation_gain_m = models.PositiveIntegerField()

    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    duration_type = models.CharField(max_length=20, choices=DURATION_CHOICES)

    popularity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )

    gear = models.ManyToManyField(Gear, blank=True)

    mountain_range = models.ForeignKey(MountainRange, on_delete=models.PROTECT, related_name='routes')
    starting_point = models.ForeignKey(StartingPoint, on_delete=models.PROTECT, related_name='routes')

    def __str__(self):
        return self.name
