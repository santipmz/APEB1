# Comprobaciones iniciales

Fecha: 23 de octubre de 2026.

Entorno: Windows, Python 3.11.3. Comando reproducible desde esta carpeta:

```powershell
python -m unittest -v test_subastas.py
```

| Comprobación automatizada | Resultado |
|---|---|
| Conversión a centavos y rechazo de montos inválidos | Correcto |
| 100 ofertas mediante 20 trabajadores concurrentes, empate y rechazo tras cierre | Correcto |
| Reenvío del mismo identificador sin aplicar dos veces la oferta | Correcto |
| Un datagrama multicast recibido por dos sockets suscritos al grupo | Correcto |

La ejecución inicial en el entorno restringido agotó el tiempo de recepción multicast. Al ejecutar con autorización fuera de ese entorno, las cuatro pruebas pasaron. No se modificó el firewall.

Estas comprobaciones verifican la lógica compartida y los sockets multicast locales. Aún no verifican la interacción completa de las consolas ni la comunicación entre equipos. Las ofertas concurrentes de esta prueba se aplican directamente a la lógica del servidor; queda pendiente reproducirlas con clientes conectados por TCP.

Pendientes: prueba manual con varias ventanas, prueba entre dos equipos por ZeroTier, ejecución de cinco clientes y capturas de Wireshark de cada integrante.
