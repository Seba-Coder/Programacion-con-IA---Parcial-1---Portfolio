"""
Servidor MCP para juego de Batalla Naval en Python usando FastMCP.
"""

import random
from typing import Dict, List, Tuple, Set, Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Batalla Naval MCP")

# --- Constantes y Configuración del Juego ---
BOARD_SIZE = 6
SHIP_SIZES = [3, 2, 1]  # 3 barcos: 3 casillas, 2 casillas, 1 casilla

# --- Estado Global del Juego ---
class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        # Barcos: conjunto de tuplas (x, y) ocupadas por barcos
        # Mapeo de barco_id a conjunto de coordenadas para verificar cuando se hunde
        self.player_ships: List[Set[Tuple[int, int]]] = []
        self.ai_ships: List[Set[Tuple[int, int]]] = []

        # Coordenadas ocupadas totales
        self.player_ship_coords: Set[Tuple[int, int]] = set()
        self.ai_ship_coords: Set[Tuple[int, int]] = set()

        # Tiros realizados (x, y)
        self.player_shots: Set[Tuple[int, int]] = set()
        self.ai_shots: Set[Tuple[int, int]] = set()

        # Impactos
        self.player_hits: Set[Tuple[int, int]] = set()
        self.ai_hits: Set[Tuple[int, int]] = set()

        # IA State: 'caza' o 'persecucion'
        self.ai_mode: str = "caza"
        self.ai_target_queue: List[Tuple[int, int]] = []
        
        # Generar tableros
        self.player_ships, self.player_ship_coords = self._generate_board()
        self.ai_ships, self.ai_ship_coords = self._generate_board()

    def _generate_board(self) -> Tuple[List[Set[Tuple[int, int]]], Set[Tuple[int, int]]]:
        """Genera barcos aleatorios sin superposición ni adyacencia (horizontal/vertical/diagonal)."""
        all_ships: List[Set[Tuple[int, int]]] = []
        occupied: Set[Tuple[int, int]] = set()
        forbidden: Set[Tuple[int, int]] = set()

        for size in SHIP_SIZES:
            placed = False
            attempts = 0
            while not placed and attempts < 500:
                attempts += 1
                orientation = random.choice(["H", "V"])
                if orientation == "H":
                    start_x = random.randint(0, BOARD_SIZE - size)
                    start_y = random.randint(0, BOARD_SIZE - 1)
                    coords = {(start_x + i, start_y) for i in range(size)}
                else:
                    start_x = random.randint(0, BOARD_SIZE - 1)
                    start_y = random.randint(0, BOARD_SIZE - size)
                    coords = {(start_x, start_y + i) for i in range(size)}

                # Verificar si interseca con casillas ocupadas o prohibidas (adyacentes)
                if any(c in forbidden or c in occupied for c in coords):
                    continue

                # Colocado exitosamente
                all_ships.append(coords)
                occupied.update(coords)

                # Marcar zonas prohibidas (casillas ocupadas y sus 8 vecinos)
                for cx, cy in coords:
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            nx, ny = cx + dx, cy + dy
                            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                                forbidden.add((nx, ny))

                placed = True

            if not placed:
                # Reiniciar si por azar quedó acorralado
                return self._generate_board()

        return all_ships, occupied

game_state = GameState()


# --- MCP Resource ---
@mcp.resource("battleship://reglas")
def obtener_reglas() -> str:
    """Devuelve las reglas oficiales de la partida de Batalla Naval MCP."""
    return (
        "=== REGLAS DE BATALLA NAVAL MCP ===\n"
        "- Tablero: Matriz de 6x6 (coordenadas x=0..5, y=0..5).\n"
        "- Barcos por jugador: 3 barcos (uno de 3 casillas, uno de 2 casillas y uno de 1 casilla).\n"
        "- Ubicación: Colocados horizontal o verticalmente sin superponerse ni tocarse (incluso en diagonales).\n"
        "- Turnos: El jugador humano dispara indicando coordenadas (x, y) a la IA con 'disparar_a_ia'.\n"
        "  Luego, la IA responde disparando automáticamente al tablero del jugador con 'disparar_a_jugador'.\n"
        "- Resultados de disparo: 'agua', 'tocado' o 'hundido'.\n"
        "- Condición de victoria: Gana el primero en hundir todos los barcos del rival."
    )


# --- MCP Tools ---
@mcp.tool()
def iniciar_partida() -> str:
    """Genera ambos tableros al azar respetando las reglas de ubicación y resetea todo el estado."""
    game_state.reset()
    return "Nueva partida iniciada. Ambos tableros fueron generados y el estado fue reseteado."


@mcp.tool()
def disparar_a_ia(x: int, y: int) -> str:
    """
    Recibe las coordenadas (x, y) donde el jugador desea disparar contra la IA.
    Valida las coordenadas, revisa si impacta y devuelve 'agua', 'tocado' o 'hundido'.
    """
    if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
        return f"Error: Coordenadas ({x}, {y}) fuera de rango (0 a 5)."

    coord = (x, y)
    if coord in game_state.player_shots:
        return f"Ya habías disparado anteriormente en la coordenada ({x}, {y}). Elegí otra."

    game_state.player_shots.add(coord)

    # Recomprobar si impacta en algún barco de la IA
    if coord in game_state.ai_ship_coords:
        game_state.player_hits.add(coord)
        
        # Verificar si el barco específico fue completado (hundido)
        for ship in game_state.ai_ships:
            if coord in ship:
                if ship.issubset(game_state.player_hits):
                    return f"¡Impacto en ({x}, {y})! HUNDIDO. Hundiste un barco de la IA de tamaño {len(ship)}."
                else:
                    return f"¡Impacto en ({x}, {y})! TOCADO."

    return f"Disparo en ({x}, {y}): AGUA."


@mcp.tool()
def disparar_a_jugador() -> str:
    """
    Sin parámetros. Decide la coordenada automáticamente con lógica hunt-and-target.
    Si hay celdas pendientes en la cola de persecución, dispara allí. Si no, elige al azar.
    Agrega celdas adyacentes no probadas en caso de 'tocado'. Si lo hunde, vacía la cola.
    """
    # Determinar siguiente objetivo
    target: Optional[Tuple[int, int]] = None

    while game_state.ai_target_queue:
        candidate = game_state.ai_target_queue.pop(0)
        if candidate not in game_state.ai_shots:
            target = candidate
            break

    # Si no hay objetivos válidos en la cola, cambiar a modo caza
    if target is None:
        game_state.ai_mode = "caza"
        untried = [
            (x, y)
            for x in range(BOARD_SIZE)
            for y in range(BOARD_SIZE)
            if (x, y) not in game_state.ai_shots
        ]
        if not untried:
            return "La IA no tiene casillas disponibles para disparar."
        target = random.choice(untried)

    x, y = target
    game_state.ai_shots.add(target)

    # Evaluar disparo en el tablero del jugador
    if target in game_state.player_ship_coords:
        game_state.ai_hits.add(target)

        # Buscar qué barco del jugador fue impactado
        for ship in game_state.player_ships:
            if target in ship:
                if ship.issubset(game_state.ai_hits):
                    # Hundido -> vaciar cola de objetivos y volver a modo caza
                    game_state.ai_mode = "caza"
                    game_state.ai_target_queue.clear()
                    return f"La IA disparó en ({x}, {y}): HUNDIDO un barco tuyo de tamaño {len(ship)}."
                else:
                    # Tocado -> Entrar/mantener modo persecución y agregar 4 adyacentes
                    game_state.ai_mode = "persecucion"
                    adjacent = [
                        (x + 1, y), (x - 1, y),
                        (x, y + 1), (x, y - 1)
                    ]
                    for adj in adjacent:
                        ax, ay = adj
                        if 0 <= ax < BOARD_SIZE and 0 <= ay < BOARD_SIZE:
                            if adj not in game_state.ai_shots and adj not in game_state.ai_target_queue:
                                game_state.ai_target_queue.append(adj)
                    return f"La IA disparó en ({x}, {y}): TOCADO."

    return f"La IA disparó en ({x}, {y}): AGUA."


@mcp.tool()
def obtener_estado_partida() -> Dict:
    """
    Devuelve la representación en caracteres/diccionario de ambos tableros.
    El tablero del jugador se ve completo. De la IA solo se muestran los disparos e impactos descubiertos.
    """
    player_grid = []
    for y in range(BOARD_SIZE):
        row = []
        for x in range(BOARD_SIZE):
            coord = (x, y)
            if coord in game_state.player_hits:
                row.append("X")  # Tocado / Hundido
            elif coord in game_state.player_shots:
                row.append("O")  # Agua
            elif coord in game_state.player_ship_coords:
                row.append("B")  # Barco visible
            else:
                row.append("~")  # Agua oculta
        player_grid.append(" ".join(row))

    ai_grid = []
    for y in range(BOARD_SIZE):
        row = []
        for x in range(BOARD_SIZE):
            coord = (x, y)
            if coord in game_state.ai_hits:
                row.append("X")  # Tocado / Hundido
            elif coord in game_state.player_shots:
                row.append("O")  # Agua
            else:
                row.append("~")  # Oculto / Desconocido
        ai_grid.append(" ".join(row))

    return {
        "tablero_jugador": player_grid,
        "tablero_ia_descubierto": ai_grid,
        "modo_ia": game_state.ai_mode,
        "cola_persecucion_ia": [f"({x},{y})" for x, y in game_state.ai_target_queue],
        "leyenda": "~: Oculto/Agua, B: Barco tuyo, O: Disparo al agua, X: Disparo acertado"
    }


@mcp.tool()
def verificar_fin_juego() -> str:
    """Verifica si algún jugador ya hundió todos los barcos del otro."""
    player_won = game_state.ai_ship_coords.issubset(game_state.player_hits)
    ai_won = game_state.player_ship_coords.issubset(game_state.ai_hits)

    if player_won and ai_won:
        return "¡Empate! Ambos hundieron el último barco en el mismo turno."
    elif player_won:
        return "¡Ganaste la partida! Hundiste todos los barcos de la IA."
    elif ai_won:
        return "¡La IA ganó la partida! Hundió todos tus barcos."
    else:
        return "La partida continúa. Aún hay barcos a flote en ambos lados."

#función que cuenta el total de disparos hechos por el jugador e ia
def contar_disparos_totales() -> int:
    """Devuelve el total de disparos hechos por el jugador e ia"""
    return len(game_state.player_shots) + len(game_state.ai_shots)

def calcular_barcos_restantes(tablero: List[List[int]]) -> int:
    """
    Calcula cuántos barcos quedan a flote en el tablero.
    Un barco se considera a flote si le queda al menos 1 casilla sin destruir.
    """
    # Contadores de casillas encontradas por tamaño/identificador de barco
    conteo_celdas = {tamaño: 0 for tamaño in SHIP_SIZES}

    # Un único recorrido de la matriz
    for fila in tablero:
        for celda in fila:
            if celda in conteo_celdas:
                conteo_celdas[celda] += 1

    # Un barco sigue a flote si el número de casillas encontradas coincide con su tamaño total
    barcos_restantes = sum(
        1 for tamaño in SHIP_SIZES if conteo_celdas[tamaño] == tamaño
    )

    return barcos_restantes


if __name__ == "__main__":
    # Inicia el servidor FastMCP usando stdio por defecto
    mcp.run()

