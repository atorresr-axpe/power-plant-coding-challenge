from fastapi import FastAPI, Request, HTTPException
import traceback
from datetime import datetime
from typing import Any, Dict
import json
import os
import logging


import os
import logging

def setup_logger():
    # Crear carpeta si no existe
    folder_path = "logs"
    os.makedirs(folder_path, exist_ok=True)

    # Crear archivo si no existe
    file_path = os.path.join(folder_path, "app.log")
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            pass  # crea el archivo vacío

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),                      # Muestra en consola
            logging.FileHandler(file_path, mode='a')      # Guarda en logs/app.log
        ]
    )

    return logging.getLogger(__name__)  # Devuelve el logger

def validar_payload(payload: Dict[str, Any]) -> bool:
    # 1. Validar claves principales
    claves_principales = ['load', 'fuels', 'powerplants']
    for clave in claves_principales:
        if clave not in payload:
            raise ValueError(f"Falta la clave principal: '{clave}'")

    # 2. Validar 'load' como número (entero o flotante)
    if not isinstance(payload['load'], (int, float)):
        raise TypeError("La clave 'load' debe ser un número (int o float)")

    # 3. Validar 'fuels'
    claves_fuels = ['gas(euro/MWh)', 'kerosine(euro/MWh)', 'co2(euro/ton)', 'wind(%)']
    fuels = payload['fuels']
    if not isinstance(fuels, dict):
        raise TypeError("La clave 'fuels' debe ser un diccionario")

    for clave in claves_fuels:
        if clave not in fuels:
            raise ValueError(f"Falta la clave de 'fuels': '{clave}'")
        if not isinstance(fuels[clave], (int, float)):
            raise TypeError(f"El valor de '{clave}' en 'fuels' debe ser numérico")

    # 4. Validar 'powerplants'
    powerplants = payload['powerplants']
    if not isinstance(powerplants, list):
        raise TypeError("La clave 'powerplants' debe ser una lista")

    claves_plantas = ['name', 'type', 'efficiency', 'pmin', 'pmax']
    for i, planta in enumerate(powerplants):
        if not isinstance(planta, dict):
            raise TypeError(f"Cada 'powerplant' debe ser un diccionario (índice {i})")
        for clave in claves_plantas:
            if clave not in planta:
                raise ValueError(f"Falta la clave '{clave}' en 'powerplant' (índice {i})")
    return True


def al_production_plan(payload):
    load = payload["load"]
    fuels = payload["fuels"]
    plants = payload["powerplants"]
    wind_pct = fuels.get("wind(%)", 0)

    # 1. Filter out wind turbines if wind% = 0
    usable = []
    for plant in plants:
        if plant["type"] == "windturbine" and wind_pct == 0:
            # Skip wind turbines when wind is zero
            continue
        # Otherwise keep plant (we could also cap its pmax by wind%, but here just exclude if wind=0)
        usable.append(plant)

    N = len(usable)
    names = [p["name"] for p in usable]
    pmin = [p["pmin"] for p in usable]
    pmax = [p["pmax"] for p in usable]

    # 2. Recursive backtracking to select a subset of plants
    solution = None  # will hold index list of chosen plants
    
    def backtrack(i, chosen, sum_min, sum_max):
        nonlocal solution
        # If we already found a solution, stop
        if solution is not None:
            return
        # If sum of mins > load, this branch cannot work
        if sum_min > load:
            return
        # If we've considered all plants:
        if i == N:
            # Check if we can exactly meet the load with chosen plants
            if sum_min <= load <= sum_max:
                solution = list(chosen)  # record this valid subset
            return
        # Option 1: Exclude plant i (set it to 0)
        backtrack(i+1, chosen, sum_min, sum_max)
        # Option 2: Include plant i (must produce at least pmin[i])
        # Only proceed if including it doesn't already exceed the load by its pmin
        if sum_min + pmin[i] <= load:
            chosen.append(i)
            backtrack(i+1, chosen, sum_min + pmin[i], sum_max + pmax[i])
            chosen.pop()

    backtrack(0, [], 0.0, 0.0)

    # 3. If no solution found (should not happen for valid inputs), return zeros
    if solution is None:
        # Fallback: set all outputs to 0 (or raise error)
        return [{"name": name, "p": 0.0} for name in names]

    # 4. Distribute remaining load among chosen plants
    output = {name: 0.0 for name in names}
    total_min = 0.0
    for i in solution:
        output[names[i]] = pmin[i]
        total_min += pmin[i]
    remainder = load - total_min
    # Greedily fill up to pmax
    for i in solution:
        if remainder <= 0:
            break
        avail = pmax[i] - pmin[i]
        add = min(avail, remainder)
        output[names[i]] += add
        remainder -= add

    # 5. Round to one decimal and adjust for any tiny rounding error
    #    (to ensure sum equals load exactly)
    plan = []
    for name in names:
        pval = round(output[name] + 1e-9, 1)
        plan.append({"name": name, "p": pval})
    # Fix rounding drift if any (typically ±0.1)
    diff = load - sum(item["p"] for item in plan)
    diff = round(diff, 1)
    if abs(diff) >= 0.1:
        # Adjust the first plant that can absorb the difference
        for item in plan:
            name = item["name"]
            # Find its index and bounds
            idx = names.index(name)
            low = 0.0
            high = pmax[idx]
            # Only adjust if within bounds
            if low <= item["p"] + diff <= high:
                item["p"] = round(item["p"] + diff, 1)
                break

    return plan


app = FastAPI()

@app.post("/productionplan")
async def production_plan(request: Request): #Representa la petición HTTP a la 
    logger = setup_logger()
    logger.info("Logger started successfully")

    try:
        payload = await request.json()

        logger.info("Starting the structure and type validation process")

        if validar_payload(payload):

            logger.info("Data type and structure are correct")
            
            logger.info("The optimization algorithm is about to start")
            
            results = al_production_plan(payload)

            logger.info("Optimization algorithm finished. Process completed successfully.")

            with open("response.json","w") as f:
                json.dump(results,f,indent=4)
            
            logger.info("Correctly generated data. Process successfully completed.")
        
    except Exception as e:
        logger.error(f"An Exception has occurred: {str(e)}")

        




