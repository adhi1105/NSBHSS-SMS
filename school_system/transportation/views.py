from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages  # This was missing!
from .models import Route, TransportSubscription, Vehicle
from .forms import VehicleForm, RouteForm

@login_required
def index(request):
    # ADMIN VIEW: Fleet Overview
    if request.user.is_superuser or request.user.groups.filter(name='Admin').exists():
        routes = Route.objects.all()
        vehicles = Vehicle.objects.all()
        total_students = TransportSubscription.objects.filter(is_active=True).count()
        
        return render(request, 'transportation/admin_dashboard.html', {
            'routes': routes,
            'vehicles': vehicles,
            'total_students': total_students
        })

    # STUDENT VIEW: My Bus Details
    else:
        try:
            # Try to get student profile safely
            student = getattr(request.user, 'student', None) or getattr(request.user, 'student_profile', None)
            
            if not student:
                return render(request, 'dashboard/error.html', {'message': "No Student Profile Found"})

            subscription = TransportSubscription.objects.filter(student=student, is_active=True).first()
            return render(request, 'transportation/my_transport.html', {'sub': subscription})
            
        except Exception as e:
            return render(request, 'dashboard/error.html', {'message': str(e)})
        
@login_required
def create_vehicle(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle added to fleet successfully!")
            return redirect('transportation:index')
    else:
        form = VehicleForm()
    return render(request, 'transportation/vehicle_form.html', {'form': form, 'title': 'Add New Vehicle'})

@login_required
def create_route(request):
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "New Route created successfully!")
            return redirect('transportation:index')
    else:
        form = RouteForm()
    return render(request, 'transportation/route_form.html', {'form': form, 'title': 'Create New Route'})
@login_required
def edit_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle updated successfully!")
            return redirect('transportation:index')
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, 'transportation/vehicle_form.html', {'form': form, 'title': 'Edit Vehicle'})

@login_required
def edit_route(request, pk):
    route = get_object_or_404(Route, pk=pk)
    if request.method == 'POST':
        form = RouteForm(request.POST, instance=route)
        if form.is_valid():
            form.save()
            messages.success(request, "Route updated successfully!")
            return redirect('transportation:index')
    else:
        form = RouteForm(instance=route)
    return render(request, 'transportation/route_form.html', {'form': form, 'title': 'Edit Route'})