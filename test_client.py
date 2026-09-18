"""
Client script interactivo para probar localmente el servidor MCP de Batalla Naval por consola.
"""

import sys
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["battleship.py"],
        env=None
    )

    print("Conectando con el servidor MCP de Batalla Naval...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Leer las reglas usando el resource
            print("\n--- Leyendo Recurso: battleship://reglas ---")
            reglas_result = await session.read_resource("battleship://reglas")
            for content in reglas_result.contents:
                print(content.text)

            # Iniciar partida
            print("\n--- Iniciando Partida ---")
            res_init = await session.call_tool("iniciar_partida", {})
            print(res_init.content[0].text)

            # Bucle del juego
            while True:
                # Obtener y mostrar estado
                res_estado = await session.call_tool("obtener_estado_partida", {})
                print("\n" + "="*40)
                print("ESTADO DEL JUEGO:")
                import json
                print(res_estado.content[0].text)

                # Verificar fin de juego
                res_fin = await session.call_tool("verificar_fin_juego", {})
                fin_msg = res_fin.content[0].text
                print(f"Estado de victoria: {fin_msg}")

                if "Ganaste" in fin_msg or "La IA ganó" in fin_msg or "Empate" in fin_msg:
                    print("\n¡Fin de la partida!")
                    break

                # Solicitud de entrada al usuario por consola
                try:
                    entrada = input("\nIngresá tu disparo (formato 'x y', ej. '2 3') o 'q' para salir: ").strip()
                    if entrada.lower() == 'q':
                        print("Partida terminada por el jugador.")
                        break

                    partes = entrada.split()
                    if len(partes) != 2:
                        print("Por favor, ingresá 2 números separados por espacio.")
                        continue

                    x, y = int(partes[0]), int(partes[1])
                except ValueError:
                    print("Entrada no válida. Asegurate de ingresar dos números enteros.")
                    continue
                except KeyboardInterrupt:
                    break

                # 1. Disparo del jugador
                res_jugador = await session.call_tool("disparar_a_ia", {"x": x, "y": y})
                print(f"\nResultado de tu disparo: {res_jugador.content[0].text}")

                # Verificar fin de juego tras el disparo del jugador
                res_fin = await session.call_tool("verificar_fin_juego", {})
                if "Ganaste" in res_fin.content[0].text:
                    print(f"\n¡{res_fin.content[0].text}!")
                    break

                # 2. Disparo automático de la IA
                res_ia = await session.call_tool("disparar_a_jugador", {})
                print(f"Resultado del disparo de la IA: {res_ia.content[0].text}")

if __name__ == "__main__":
    asyncio.run(main())
