# APEB1 — Sistema de subastas en vivo

Primera etapa: implementación y prueba local. Requiere Python 3.11 o posterior, sin paquetes externos.

## Prueba en Windows

Abra tres terminales en esta carpeta. En la primera:

Por defecto se utiliza la IP que Windows resuelve para el nombre del equipo. El subastador la muestra al iniciar. Si hay varios adaptadores, seleccione la IP correcta mediante `--interfaz` y use esa misma IP en `--servidor` del cliente. Para esta prueba multicast local seleccionamos la IP del adaptador del equipo.

```powershell
python subastas.py subastador --precio 100.00
```

En la segunda:

```powershell
python subastas.py cliente --nombre "Santiago"
```

En la tercera:

```powershell
python subastas.py cliente --nombre "Cliente de prueba"
```

En un cliente escriba `110`, en el otro `120`. Verifique que ambos muestran el precio 120. Pruebe `115`: debe rechazarse. En el subastador escriba `cerrar`. Verifique el ganador y pruebe una nueva oferta: debe rechazarse. Mantenga el servidor abierto hasta verificar el cierre en todos los clientes. `estado` consulta el estado actual; `salir` termina el proceso.

Los anuncios se repiten cada dos segundos. Para observar una recepción identificada como MULTICAST, envíe una puja desde otro cliente: la respuesta al oferente también llega por TCP y puede mostrarse antes que el anuncio multicast.

## Diseño

- TCP 5000: identificación, ofertas, respuestas y consulta de estado. JSON UTF-8, un mensaje por línea.
- UDP 5001, grupo 239.255.42.99: anuncios multicast con estado completo y versión creciente. TTL 1 y recepción local habilitada.
- Un hilo por conexión TCP, otro para anuncios periódicos y recepción independiente en clientes.
- Un bloqueo protege la validación, modificación y cierre de la subasta; otro serializa anuncios. La espera de red queda fuera del bloqueo del estado.
- Montos enteros en centavos. Una oferta empatada se rechaza. El orden es el de procesamiento en el servidor, no necesariamente el de envío.
- Identificador de oferta para evitar volver a aplicar una solicitud repetida durante la misma ejecución.
- El servidor permanece disponible tras cerrar para consultar el resultado. Los anuncios UDP no garantizan entrega; la repetición y consulta TCP recuperan el estado.

## Siguiente etapa: red virtual

Primero probar entre dos equipos y después entre los cinco. Todos deben usar el mismo grupo y puertos. Ejemplo de parámetros (reemplace las IP por las reales):

```powershell
python subastas.py subastador --interfaz IP_VIRTUAL_SUBASTADOR
python subastas.py cliente --interfaz IP_VIRTUAL_CLIENTE --servidor IP_VIRTUAL_SUBASTADOR --nombre "Nombre completo"
```

El cliente que comparte equipo con el subastador usa la misma IP virtual en ambos parámetros. Comprobar membresía y multicast en ZeroTier y permitir los puertos de la aplicación en el firewall de Windows. No es necesario desactivar el firewall.

## Evidencias pendientes

Las pruebas locales no sustituyen las pruebas grupales exigidas. No se han realizado aún las pruebas con compañeros ni capturas de Wireshark.

En Wireshark seleccione el adaptador virtual, fecha y hora UTC y precisión de nanosegundos. Filtro de visualización: `ip.dst == 239.255.42.99 && udp.port == 5001`. Para el control: `tcp.port == 5000`. La precisión seleccionada de visualización no garantiza que la fuente de captura mida con exactitud de nanosegundos.

Guardar capturas de cada integrante y archivos pcapng. Relacionar ofertas, respuestas y anuncios mediante sus campos; registrar pérdida o saltos observados y latencias solo cuando los relojes y la captura permitan interpretarlas.

## Alcance

Prototipo académico para una red de participantes conocidos. No incorpora autenticación, persistencia, reconexión automática ni protección para uso público. Los nombres deben ser únicos durante las pruebas. Al reiniciar el servidor, reinicie también los clientes.
