from django.db import models
from django.utils.timezone import now
from django.core.validators import MaxValueValidator, MinValueValidator


class CarMake(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    founded_year = models.IntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1886),  # First car was made in 1886
            MaxValueValidator(now().year)
        ]
    )
    headquarters = models.CharField(max_length=100, blank=True)
    website = models.URLField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Car Make"
        verbose_name_plural = "Car Makes"


class CarModel(models.Model):
    # Car type choices
    CAR_TYPES = [
        ('SEDAN', 'Sedan'),
        ('SUV', 'SUV'),
        ('WAGON', 'Wagon'),
        ('COUPE', 'Coupe'),
        ('CONVERTIBLE', 'Convertible'),
        ('TRUCK', 'Truck'),
        ('VAN', 'Van'),
        ('HATCHBACK', 'Hatchback'),
        ('ELECTRIC', 'Electric'),
        ('HYBRID', 'Hybrid'),
    ]

    # Fields
    car_make = models.ForeignKey(CarMake, on_delete=models.CASCADE)
    dealer_id = models.IntegerField(
        validators=[MinValueValidator(1)]
    )
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=CAR_TYPES, default='SUV')
    year = models.IntegerField(
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(now().year + 1)  # Allow next year's models
        ]
    )
    engine = models.CharField(max_length=50, blank=True)
    trim_level = models.CharField(max_length=50, blank=True)
    mpg_city = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    mpg_highway = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.car_make.name} {self.name} ({self.year})"

    class Meta:
        verbose_name = "Car Model"
        verbose_name_plural = "Car Models"
        ordering = ['car_make', 'name', '-year']
        constraints = [
            models.UniqueConstraint(
                fields=['car_make', 'name', 'year'],
                name='unique_model_year'
            )
        ]
    