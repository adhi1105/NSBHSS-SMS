from django.db import models
from django.utils import timezone
from student_info.models import Student

# --- 1. FLEET MANAGEMENT ---
class Driver(models.Model):
    name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=15)
    
    def __str__(self):
        return f"{self.name} ({self.license_number})"

class Vehicle(models.Model):
    vehicle_no = models.CharField(max_length=20, unique=True) # e.g., "KL-01-AB-1234"
    model_name = models.CharField(max_length=50)              # e.g., "Tata Starbus"
    capacity = models.IntegerField(default=40)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Maintenance Alerts
    insurance_expiry = models.DateField()
    pollution_expiry = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.vehicle_no} - {self.model_name}"

    def needs_maintenance(self):
        # Alert if expiry is within 30 days
        today = timezone.now().date()
        warning_date = today + timezone.timedelta(days=30)
        return self.insurance_expiry <= warning_date or self.pollution_expiry <= warning_date

# --- 2. ROUTE & PRICING ---
class Route(models.Model):
    name = models.CharField(max_length=100)      # e.g., "Route 5 - North Zone"
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True)
    start_point = models.CharField(max_length=100)
    end_point = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Stop(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    stop_name = models.CharField(max_length=100) # e.g., "City Center Mall"
    pickup_time = models.TimeField()
    drop_time = models.TimeField()
    
    # Zone-Based Pricing
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)

    def __str__(self):
        return f"{self.stop_name} (Fee: {self.monthly_fee})"

# --- 3. STUDENT SUBSCRIPTION ---
class TransportSubscription(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='transport')
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True)
    stop = models.ForeignKey(Stop, on_delete=models.SET_NULL, null=True)
    
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.route.name}"