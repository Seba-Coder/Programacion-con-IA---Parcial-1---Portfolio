# Batalla Naval MCP

Proyecto de un juego de Batalla Naval jugado por chat entre un jugador humano y una IA, implementado a través de un servidor propio con el SDK oficial de MCP (`mcp.server.fastmcp`).

---

## 📌 Razón de Elección de MCP Propio

Se desarrolló un servidor MCP propio debido a que **no existe un servidor MCP específico de la comunidad para Batalla Naval** que gestione el estado del tablero y aplique una estrategia *Hunt-and-Target* automatizada. Además, permite demostrar el ciclo completo de diseño e integración de herramientas (*tools*) y recursos (*resources*) con el protocolo MCP.

---

## 🚀 Requisitos e Instalación

- **Python**: 3.10+ (probado en Python 3.11).
- **Dependencias**:

```bash
pip install -r requirements.txt
```

*(Instala `mcp<2` para garantizar compatibilidad con FastMCP).*

---

## 💻 Ejecución Standalone

Podés probar el servidor localmente desde la consola mediante un cliente de prueba interactivo sin necesidad de un cliente MCP complejo:

```bash
python test_client.py
```

---

## ⚙️ Configuración en Antigravity

Para conectar el servidor MCP a Antigravity y usarlo desde el chat del agente:

1. **Ubicación del archivo de configuración**:  
   `C:\Users\<Usuario>\.gemini\config\mcp_config.json`

2. **Contenido del JSON**:
   ```json
   {
     "mcpServers": {
       "battleship-mcp": {
         "command": "C:\\Users\\Seba\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
         "args": [
           "c:\\Users\\Seba\\Desktop\\Sebastian\\Universidad\\Programación con IA generativa (Electiva 1)\\Parcial 1\\battleship.py"
         ]
       }
     }
   }
   ```

3. Recargá los servidores MCP en Antigravity desde `Additional Options (...) > MCP Servers` o reiniciando la aplicación.

---

## 🛠️ Tools y Resource

### 📖 Resource (Solo lectura)
- `battleship://reglas`: Devuelve las reglas oficiales de la partida (dimensiones 6x6, barcos y condición de victoria).

### ⚙️ Tools
1. `iniciar_partida()`: Genera ambos tableros al azar cumpliendo las reglas de posición y resetea el estado global.
2. `disparar_a_ia(x, y)`: Recibe coordenadas del jugador, valida el disparo y devuelve `"agua"`, `"tocado"` o `"hundido"`.
3. `disparar_a_jugador()`: Decide y ejecuta automáticamente el disparo de la IA usando la lógica *Hunt-and-Target*.
4. `obtener_estado_partida()`: Devuelve el tablero completo del jugador y el tablero descubierto de la IA.
5. `verificar_fin_juego()`: Comprueba si algún jugador hundió todos los barcos del rival y declara al ganador.

---

## 🧠 Algoritmo Hunt-and-Target de la IA

La IA opera con un autómata de estados de dos modos:
1. **Modo Caza (*Hunt*)**: Elige casillas aleatorias no probadas del tablero del jugador hasta lograr un impacto.
2. **Modo Persecución (*Target*)**: Al hacer un disparo `"tocado"`, cambia a modo persecución y añade las 4 celdas adyacentes no probadas a una cola de objetivos pendientes. Prioriza disparar a esa cola. Al `"hundir"` el barco, vacía la cola y regresa al modo caza.

---

## 📂 Estructura de Archivos

```text
Parcial 1/
├── battleship.py        # Servidor MCP, estado global, algoritmo IA y definión de tools/resource
├── test_client.py       # Cliente interactivo de consola para pruebas standalone vía STDIO
├── requirements.txt     # Dependencias de Python (mcp<2)
├── README.md            # Documentación del proyecto
└── .vscode/
    └── settings.json    # Configuración del intérprete de Python para el IDE
```

## 🤖 Evidencia de Flujos de IA en el Editor

- **Autocompletado**: la función `contar_disparos_totales()` en `battleship.py` fue generada por autocompletado del editor a partir del nombre y tipo de retorno escritos manualmente.
- **Refactorización guiada**: se le pidió a la IA que escribiera la función `calcular_barcos_restantes()` intencionalmente con mala práctica (números mágicos, nombres poco descriptivos, lógica repetida) para luego refactorizarla aplicando buenas prácticas. La versión original sin refactorizar se conserva en `battleship_pre_refactorizacion.py` como evidencia comparativa; la versión final y funcional está en `battleship.py`.
