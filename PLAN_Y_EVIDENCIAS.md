# Seguimiento APEB1

## Integrantes

| Nombre | IP virtual de prueba | Participación evaluada |
|---|---|---|
| Alvarado Castillo Alex Gerardo | Pendiente | Pendiente |
| Asero Tipanluisa Gonzalo Rodrigo | Pendiente | Pendiente |
| Coloma Flores Darwin Joan | Pendiente | Pendiente |
| Muñoz Torres Adriano Alberto | Pendiente | Pendiente |
| Muñoz Zurita Santiago Patricio | Pendiente | Pendiente |

## Secuencia de trabajo y rúbrica

1. Implementación (2 puntos): revisar código, probar ofertas inválidas, empates, concurrencia y cierre.
2. Prueba local: un subastador y varios clientes en el equipo del organizador. Registrar resultados reales.
3. Red virtual (3 puntos): instalar y configurar ZeroTier; comprobar primero dos equipos y luego los cinco. El organizador ejecuta también su cliente.
4. Wireshark (4 puntos): cada estudiante captura su tráfico, muestra fecha y hora UTC y nanosegundos, identifica destino multicast, puertos y contenido, e interpreta los resultados. Guardar pcapng y capturas legibles.
5. Informe y originalidad (1 punto): tabla de integrantes/IP/participación, introducción, desarrollo, pruebas y resultados, conclusiones personales y bibliografía APA. Redactar a partir de lo realizado; comprobar similitud con la herramienta institucional.

## Registro de pruebas grupales (por completar)

| Prueba | Resultado esperado | Resultado observado | Evidencia |
|---|---|---|---|
| Cinco clientes conectados | Todos reciben el estado | Pendiente | Pendiente |
| Oferta superior | Aceptada y anunciada a todos | Pendiente | Pendiente |
| Oferta inferior o igual | Rechazada, precio sin cambios | Pendiente | Pendiente |
| Ofertas simultáneas | Precio final máximo válido | Pendiente | Pendiente |
| Cierre | Ganador consistente, nuevas ofertas rechazadas | Pendiente | Pendiente |
| Recuperación de estado | Consulta TCP devuelve estado vigente | Pendiente | Pendiente |

## Análisis costo-beneficio para el informe

Comparar el servidor en un equipo existente frente a un servidor dedicado: costo de equipo, energía, instalación, mantenimiento, disponibilidad y capacidad. Justificar la alternativa académica con cinco clientes usando observaciones reales; no asignar cifras de rendimiento sin medirlas. Considerar que apagar el equipo subastador detiene el servicio.

## Fuentes técnicas iniciales

- Python Software Foundation. (s. f.). *socket — Low-level networking interface*. https://docs.python.org/3/library/socket.html
- Python Software Foundation. (s. f.). *threading — Thread-based parallelism*. https://docs.python.org/3/library/threading.html
- ZeroTier. (s. f.). *The protocol*. https://docs.zerotier.com/protocol/

Antes de la entrega, verificar las fuentes y completar las referencias según el formato APA solicitado por la institución.
