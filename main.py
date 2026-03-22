from fastapi import FastAPI, Query, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(title="SpeedRide Car Rentals")

# --- In-Memory Data ---
cars = [
    {"id": 1, "model": "Civic", "brand": "Honda", "type": "Sedan", "price_per_day": 5000, "fuel_type": "Petrol", "is_available": True},
    {"id": 2, "model": "Swift", "brand": "Maruti", "type": "Hatchback", "price_per_day": 3000, "fuel_type": "Petrol", "is_available": True},
    {"id": 3, "model": "Fortuner", "brand": "Toyota", "type": "SUV", "price_per_day": 12000, "fuel_type": "Diesel", "is_available": False},
    {"id": 4, "model": "S-Class", "brand": "Mercedes", "type": "Luxury", "price_per_day": 25000, "fuel_type": "Diesel", "is_available": True},
    {"id": 5, "model": "Nexon EV", "brand": "Tata", "type": "SUV", "price_per_day": 6000, "fuel_type": "Electric", "is_available": True},
    {"id": 6, "model": "i20", "brand": "Hyundai", "type": "Hatchback", "price_per_day": 3500, "fuel_type": "Petrol", "is_available": True}
]

rentals = []
rental_counter = 1

# --- Models ---
class RentalRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    car_id: int = Field(..., gt=0)
    days: int = Field(..., gt=0, le=30)
    license_number: str = Field(..., min_length=8)
    insurance: bool = False
    driver_required: bool = False

class NewCar(BaseModel):
    model: str = Field(..., min_length=2)
    brand: str = Field(..., min_length=2)
    type: str = Field(..., min_length=2)
    price_per_day: int = Field(..., gt=0)
    fuel_type: str = Field(..., min_length=2)
    is_available: bool = True

# --- Helpers ---
def find_car(car_id: int):
    return next((car for car in cars if car["id"] == car_id), None)

def calculate_rental_cost(price_per_day: int, days: int, insurance: bool, driver_required: bool):
    base_cost = price_per_day * days
    discount = 0.0
    if days >= 15:
        discount = base_cost * 0.25
    elif days >= 7:
        discount = base_cost * 0.15

    insurance_cost = (500 * days) if insurance else 0
    driver_cost = (800 * days) if driver_required else 0

    total_cost = base_cost - discount + insurance_cost + driver_cost

    return {
        "base_cost": base_cost,
        "discount": discount,
        "insurance_cost": insurance_cost,
        "driver_cost": driver_cost,
        "total_cost": total_cost
    }

def filter_cars_logic(type: Optional[str] = None, brand: Optional[str] = None, fuel_type: Optional[str] = None, max_price: Optional[int] = None, is_available: Optional[bool] = None, car_list=None):
    if car_list is None:
        car_list = cars
    result = car_list

    if type is not None:
        result = [c for c in result if c["type"].lower() == type.lower()]
    if brand is not None:
        result = [c for c in result if c["brand"].lower() == brand.lower()]
    if fuel_type is not None:
        result = [c for c in result if c["fuel_type"].lower() == fuel_type.lower()]
    if max_price is not None:
        result = [c for c in result if c["price_per_day"] <= max_price]
    if is_available is not None:
        result = [c for c in result if c["is_available"] == is_available]

    return result

# --- ENDPOINTS ---

# 1. GET /
@app.get("/")
def read_root():
    return {"message": "Welcome to SpeedRide Car Rentals"}

# 5. GET /cars/summary
@app.get("/cars/summary")
def get_cars_summary():
    available_count = sum(1 for c in cars if c["is_available"])
    
    type_breakdown = {}
    fuel_breakdown = {}
    for c in cars:
        type_breakdown[c["type"]] = type_breakdown.get(c["type"], 0) + 1
        fuel_breakdown[c["fuel_type"]] = fuel_breakdown.get(c["fuel_type"], 0) + 1

    cheapest = min(cars, key=lambda x: x["price_per_day"]) if cars else None
    most_expensive = max(cars, key=lambda x: x["price_per_day"]) if cars else None

    return {
        "total_cars": len(cars),
        "available_count": available_count,
        "breakdown_by_type": type_breakdown,
        "breakdown_by_fuel_type": fuel_breakdown,
        "cheapest_car_per_day": cheapest,
        "most_expensive_car_per_day": most_expensive
    }

# 10. GET /cars/filter
@app.get("/cars/filter")
def filter_cars(
    type: str = None,
    brand: str = None,
    fuel_type: str = None,
    max_price: int = None,
    is_available: bool = None
):
    result = cars

    if type is not None:
        result = [c for c in result if c["type"].lower() == type.lower()]

    if brand is not None:
        result = [c for c in result if c["brand"].lower() == brand.lower()]

    if fuel_type is not None:
        result = [c for c in result if c["fuel_type"].lower() == fuel_type.lower()]

    if max_price is not None:
        result = [c for c in result if c["price_per_day"] <= max_price]

    if is_available is not None:
        result = [c for c in result if c["is_available"] == is_available]

    return {"filtered_cars": result}
# 15. GET /cars/unavailable
@app.get("/cars/unavailable")
def get_cars_unavailable():
    unavailable = [c for c in cars if not c["is_available"]]
    return {"unavailable_cars": unavailable, "count": len(unavailable)}

# 16. GET /cars/search
@app.get("/cars/search")
def get_cars_search(keyword: str = Query(...)):
    keyword = keyword.lower()
    matches = [
        c for c in cars
        if keyword in c["model"].lower() or keyword in c["brand"].lower() or keyword in c["type"].lower()
    ]
    return {"matches": matches, "total_found": len(matches)}

# 17. GET /cars/sort
@app.get("/cars/sort")
def sort_cars(
    sort_by: str = Query("price_per_day"),
    order: str = Query("asc")
):
    valid_fields = ["price_per_day", "brand", "type"]

    if sort_by not in valid_fields:
        return {"error": "Invalid sort_by field"}

    reverse = True if order == "desc" else False

    sorted_cars = sorted(cars, key=lambda x: x[sort_by], reverse=reverse)

    return {
        "sort_by": sort_by,
        "order": order,
        "cars": sorted_cars
    }

# 18. GET /cars/page
@app.get("/cars/page")
def paginate_cars(page: int = 1, limit: int = 2):

    start = (page - 1) * limit
    end = start + limit

    total = len(cars)
    total_pages = (total + limit - 1) // limit

    return {
        "page": page,
        "total_pages": total_pages,
        "data": cars[start:end]
    }

# 20. GET /cars/browse
@app.get("/cars/browse")
def browse_cars(
    type: Optional[str] = None,
    max_price: Optional[int] = None,
    sort_by: str = "price_per_day",
    order: str = "asc",
    page: int = 1,
    limit: int = 2
):

    result = cars

    # filter
    if type:
        result = [c for c in result if c["type"].lower() == type.lower()]

    if max_price:
        result = [c for c in result if c["price_per_day"] <= max_price]

    # sort
    reverse = True if order == "desc" else False
    result = sorted(result, key=lambda x: x[sort_by], reverse=reverse)

    # pagination
    start = (page - 1) * limit
    end = start + limit

    return {
        "results": result[start:end],
        "total": len(result)
    }
# 2. GET /cars
@app.get("/cars")
def get_all_cars():
    available_count = sum(1 for c in cars if c["is_available"])
    return {"cars": cars, "total": len(cars), "available_count": available_count}

# 11. POST /cars
@app.post("/cars", status_code=status.HTTP_201_CREATED)
def create_car(car: NewCar):
    for c in cars:
        if c["model"].lower() == car.model.lower() and c["brand"].lower() == car.brand.lower():
            raise HTTPException(status_code=400, detail="Car with this model and brand already exists")

    new_id = max((c["id"] for c in cars), default=0) + 1
    new_car = car.dict()
    new_car["id"] = new_id
    cars.append(new_car)
    return {"message": "Car added", "car": new_car}

# 3. GET /cars/{car_id}
@app.get("/cars/{car_id}")
def get_car_by_id(car_id: int):
    car = find_car(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car

# 12. PUT /cars/{car_id}
@app.put("/cars/{car_id}")
def update_car_by_id(car_id: int, price_per_day: Optional[int] = None, is_available: Optional[bool] = None):
    car = find_car(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    if price_per_day is not None:
        car["price_per_day"] = price_per_day
    if is_available is not None:
        car["is_available"] = is_available

    return {"message": "Car updated", "car": car}

# 13. DELETE /cars/{car_id}
@app.delete("/cars/{car_id}")
def delete_car_by_id(car_id: int):
    car = find_car(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    if any(r for r in rentals if r["car_id"] == car_id and r["status"] == "active"):
        raise HTTPException(status_code=400, detail="Cannot delete car with an active rental")

    cars.remove(car)
    return {"message": f"Car {car_id} deleted"}

# --- RENTALS ENDPOINTS ---

# 15. GET /rentals/active
@app.get("/rentals/active")
def get_rentals_active():
    active = [r for r in rentals if r["status"] == "active"]
    return {"active_rentals": active, "total": len(active)}

# 19. GET /rentals/search
@app.get("/rentals/search")
def get_rentals_search(customer_name: str = Query(...)):
    matches = [r for r in rentals if customer_name.lower() in r["customer_name"].lower()]
    return {"matches": matches, "total_found": len(matches)}

# 19. GET /rentals/sort
@app.get("/rentals/sort")
def get_rentals_sort(sort_by: str = Query("total_cost")):
    valid_keys = ["total_cost", "days"]
    if sort_by not in valid_keys:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by. Allowed: {valid_keys}")

    sorted_list = sorted(rentals, key=lambda r: r[sort_by])
    return {"sorted_rentals": sorted_list, "total": len(sorted_list)}

# 19. GET /rentals/page
@app.get("/rentals/page")
def get_rentals_page(page: int = Query(1, ge=1), limit: int = Query(3, ge=1)):
    start = (page - 1) * limit
    end = start + limit
    paginated = rentals[start:end]
    return {
        "page": page,
        "limit": limit,
        "total_rentals": len(rentals),
        "total_pages": -(-len(rentals) // limit),
        "rentals": paginated
    }

# 15. GET /rentals/by-car/{car_id}
@app.get("/rentals/by-car/{car_id}")
def get_rentals_by_car(car_id: int):
    history = [r for r in rentals if r["car_id"] == car_id]
    return {"car_id": car_id, "history": history, "total": len(history)}

# 4. GET /rentals
@app.get("/rentals")
def get_all_rentals():
    return {"rentals": rentals, "total": len(rentals)}

# 14. GET /rentals/{rental_id} (Internal / Validation check)
@app.get("/rentals/{rental_id}")
def get_rental_by_id(rental_id: int):
    rental = next((r for r in rentals if r["rental_id"] == rental_id), None)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    return rental

# 8. POST /rentals
# 9. POST /rentals (Modified for driver_required)
@app.post("/rentals")
def create_rental_entry(req: RentalRequest):
    global rental_counter
    car = find_car(req.car_id)

    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    if not car["is_available"]:
        raise HTTPException(status_code=400, detail="Car is not available")

    car["is_available"] = False
    
    costs = calculate_rental_cost(car["price_per_day"], req.days, req.insurance, req.driver_required)
    
    rental_record = {
        "rental_id": rental_counter,
        "customer_name": req.customer_name,
        "car_id": req.car_id,
        "car_model": car["model"],
        "car_brand": car["brand"],
        "days": req.days,
        "license_number": req.license_number,
        "insurance": req.insurance,
        "driver_required": req.driver_required,
        "base_cost": costs["base_cost"],
        "discount": costs["discount"],
        "insurance_cost": costs["insurance_cost"],
        "driver_cost": costs["driver_cost"],
        "total_cost": costs["total_cost"],
        "status": "active"
    }

    rentals.append(rental_record)
    rental_counter += 1
    return rental_record

# 14. POST /return/{rental_id}
@app.post("/return/{rental_id}")
def return_rental_car(rental_id: int):
    rental = next((r for r in rentals if r["rental_id"] == rental_id), None)
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    if rental["status"] == "returned":
        raise HTTPException(status_code=400, detail="Rental already returned")

    rental["status"] = "returned"
    
    car = find_car(rental["car_id"])
    if car:
        car["is_available"] = True

    return {"message": "Car returned successfully", "rental": rental, "final_status": "returned"}