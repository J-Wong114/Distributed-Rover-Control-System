# http://127.0.0.1:8000/docs
import hashlib

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

app = FastAPI()

base_dir = Path(__file__).resolve().parent

template_path = str(base_dir / "templates")

templates = Jinja2Templates(directory = template_path)

# Data models
class Mine(BaseModel):
    id: Optional[int] = None
    x: int
    y: int
    serial_number: str

class MapUpdate(BaseModel):
    width: int
    height: int

class Rover(BaseModel):
    id: Optional[int] = None
    commands: str
    status: str = "Not Started" # Not Started, Started, Finished, Dead
    x: int = 0
    y: int = 0
    direction: str = "South"


# Memory storage
field_map = {"width": 5, "height": 5, "grid": [[0 for _ in range(5)] for _ in range(5)]} # Default 5x5 grid of 0s
mines_db = {} # Format: {id: MineObject}
mine_id_counter = 1

rovers_db = {} # Format: {id: RoverObject}
rover_id_counter = 1

@app.get("/", response_class = HTMLResponse)
async def read_root(request: Request):
    rovers_list = [rover.dict() for rover in rovers_db.values()]
    mines_list = [mine.dict() for mine in mines_db.values()]

    context = {
        "request": request,
        "width": int(field_map["width"]),
        "grid": field_map["grid"],
        "all_mines": mines_list,
        "all_rovers": rovers_list
    }

    return templates.TemplateResponse(name="index.html", context=context)

@app.get("/map")
def get_map():
    for row in field_map["grid"]:
        print(" ".join(map(str, row)))

    return {"width": field_map["width"], "height": field_map["height"], "map": field_map["grid"]}

@app.put("/map")
def update_map(data: MapUpdate):
    field_map["width"] = data.width
    field_map["height"] = data.height

    # Make grid of 0s (All grass tiles)
    field_map["grid"] = [[0 for _ in range(data.width)] for _ in range(data.height)]

    mines_db.clear() # The map is clear of mines at the beginning, and it should get updated upon creation, update or deletion of any mine

    return {"message": f"Map resized to {data.width}x{data.height} and all mines cleared. Map: {field_map['grid']}"}

@app.post("/mines")
def create_mine(mine: Mine):
    global mine_id_counter

    mine.id = mine_id_counter
    mines_db[mine_id_counter] = mine

    if 0 <= mine.y < len(field_map["grid"]) and 0 <= mine.x < len(field_map["grid"][0]):
        field_map["grid"][mine.y][mine.x] = 1

    mine_id_counter += 1

    return {"id": mine.id}

@app.get("/mines")
def get_all_mines():
    return list(mines_db.values())

@app.get("/mines/{mine_id}")
def get_mine(mine_id: int):
    if mine_id not in mines_db:
        raise HTTPException(status_code=404, detail="Mine not found")
    return mines_db[mine_id]

@app.delete("/mines/{mine_id}")
def delete_mine(mine_id: int):
    if mine_id in mines_db:
        del mines_db[mine_id]
        return {"message": f"Mine {mine_id} deleted"}
    raise HTTPException(status_code=404, detail="Mine not found")

@app.get("/rovers")
def get_all_rovers():
    return list(rovers_db.values())

@app.get("/rovers/{rover_id}")
def get_rover(rover_id: int):
    if rover_id not in rovers_db:
        raise HTTPException(status_code=404, detail="Rover not found")
    return rovers_db[rover_id]

@app.post("/rovers")
def create_rover(rover: Rover):
    global rover_id_counter

    if rover.id is None:
        rover.id = rover_id_counter
        rover_id_counter += 1

    rovers_db[rover.id] = rover

    return {"id": rover.id}

@app.delete("/rovers/{rover_id}")
def delete_rover(rover_id: int):
    if rover_id in rovers_db:
        del rovers_db[rover_id]
        return {"message": f"Rover {rover_id} deleted"}
    raise HTTPException(status_code=404, detail="Rover not found")

@app.put("/rovers/{rover_id}")
def update_rover(rover_id: int, update_data: Rover):
    if rover_id not in rovers_db:
        raise HTTPException(status_code=404, detail="Rover not found")

    rover = rovers_db[rover_id]

    if rover.status != "Not Started":
        raise HTTPException(status_code=400, detail="Cannot update rover that is dispatched")

    rover.commands = update_data.commands
    return{"message": f"Rover {rover_id} commands updated", "commands": rover.commands}

@app.post("/rovers/{rover_id}/dispatch")
def dispatch_rover(rover_id: int):
    if rover_id not in rovers_db:
        raise HTTPException(status_code=404, detail="Rover not found")

    rover = rovers_db[rover_id]
    rover.status = "Started"

    grid = field_map["grid"]
    height = len(grid)

    pin = None

    if height > 0:
        width = len(grid[0])
    else:
        width = 0

    # Directions: N = 0, E = 1, S = 2, W = 3
    directions = ["North", "East", "South", "West"]
    current_dir = directions.index(rover.direction)

    for cmd in rover.commands:
        if cmd == 'L':
            current_dir = (current_dir - 1) % 4
        elif cmd == 'R':
            current_dir = (current_dir + 1) % 4
        elif cmd == 'M':
            new_x, new_y = rover.x, rover.y

            if current_dir == 0: # North
                new_y -= 1
            elif current_dir == 1:  # East
                new_x += 1
            elif current_dir == 2:  # South
                new_y += 1
            elif current_dir == 3:  # West
                new_x -= 1

            if 0 <= new_x < width and 0 <= new_y < height:
                if grid[rover.y][rover.x] != 1:
                    grid[rover.y][rover.x] = "*"

                if grid[rover.y][rover.x] == 1:
                    print(f"Map value: {grid[rover.y][rover.x]}\nRover is dead")
                    rover.status = "Dead"
                    rover.direction = directions[current_dir]

                    return {"status": "Eliminated", "position": (rover.x, rover.y)}

                rover.x, rover.y = new_x, new_y
                grid[rover.y][rover.x] = "*"

        elif cmd == 'D':
            if grid[rover.y][rover.x] == 1:
                target_mine_id = None
                serial_number = None

                for m_id, mine_obj in list(mines_db.items()):
                    if mine_obj.x == rover.x and mine_obj.y == rover.y:
                        serial_number = mine_obj.serial_number
                        target_mine_id = m_id
                        break

                if serial_number:
                    pin = 0
                    while True:
                        temp_key = f"{pin}{serial_number}"
                        hash_key = hashlib.sha256(temp_key.encode()).hexdigest()
                        if hash_key.startswith("000000"):
                            if target_mine_id in mines_db:
                                del mines_db[target_mine_id]
                            grid[rover.y][rover.x] = "*"
                            break
                        pin += 1

    rover.status = "Finished"
    rover.direction = directions[current_dir]
    return {"status": rover.status, "final_position": (rover.x, rover.y), "disarm_pin": pin if "pin" in locals() else None}
