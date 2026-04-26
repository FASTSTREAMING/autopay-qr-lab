# Autopay QR Lab

Prueba aislada para validar comunicacion Android autonomo -> VPS sin tocar el bot en produccion.

## Objetivo

1. Android consulta la VPS.
2. VPS asigna un job fake.
3. Android descarga un QR fake.
4. Android guarda el QR en Descargas.
5. Android reporta estado `QR_DOWNLOADED`.

No hace pagos reales.

## Instalacion En VPS

Desde la VPS:

```bash
git clone TU_REPO_GITHUB autopay-qr-lab
cd autopay-qr-lab
./scripts/setup_vps.sh
```

Iniciar servidor de prueba:

```bash
./start_test_server.sh
```

O en segundo plano:

```bash
./start_test_server_bg.sh
```

En VPS es mejor dejarlo como servicio:

```bash
sudo ./service_start.sh
```

Ver logs:

```bash
./service_logs.sh
```

Probar:

```bash
curl http://127.0.0.1:8009/health
curl http://127.0.0.1:8009/jobs
```

Resetear job:

```bash
curl -X POST http://127.0.0.1:8009/job/TEST-0001/reset
```

Importar la ultima orden real pendiente del bot al laboratorio:

```bash
./import_latest_pending_order.sh
```

Importar un TX especifico:

```bash
./import_latest_pending_order.sh --tx-code "TX_AQUI"
```

## Tailscale

En la VPS:

```bash
tailscale up
tailscale ip -4
```

En Android instala Tailscale, inicia sesion con la misma cuenta y usa la IP `100.x.y.z`
de la VPS para `AUTOPAY_SERVER_URL`.

## Instalacion En Android Termux

Instalar en Termux:

```bash
git clone TU_REPO_GITHUB autopay-qr-lab
cd autopay-qr-lab
./scripts/setup_termux.sh
```

Nota Termux: no actualizamos `pip` dentro de Termux porque Termux lo gestiona
como paquete del sistema y bloqueara ese intento.

Ejecutar:

```bash
export AUTOPAY_SERVER_URL="http://IP_TAILSCALE_VPS:8009"
export AUTOPAY_DEVICE_ID="android-1"
./scripts/doctor_termux.sh
./scripts/run_termux_worker.sh
```

Resultado esperado: aparece `/sdcard/Download/PAY-TEST-0001.png`.

## Lanzar Tasker Automaticamente

Recomendado: en Tasker crea un Profile:

```text
Event -> Intent Received
Action: com.autopay.qr.RUN
```

Ese profile debe ejecutar tu tarea de Takenos.

En Termux:

```bash
export AUTOPAY_TASKER_INTENT_ACTION="com.autopay.qr.RUN"
export AUTOPAY_CLEAN_OLD_QR="1"
./scripts/run_termux_worker.sh
```

El worker descargara el QR y lanzara el intent. Tasker recibe variables extras:

```text
job_id
payment_id
tx_code
qr_path
```

Para reportar estados desde Termux/Tasker puedes llamar:

```bash
./scripts/post_status.sh "$job_id" PAYMENT_SUBMITTED "Takenos toco pagar"
./scripts/post_status.sh "$job_id" PAYMENT_SUCCESS_SCREEN "Takenos mostro pago exitoso"
```

Alternativa menos recomendada: llamar una Task directamente por nombre:

```bash
export AUTOPAY_TASKER_TASK="Takenos QR Prep"
```

Requiere que Tasker tenga habilitado `Allow External Access`.

## Siguiente prueba

Abrir Takenos manualmente y probar si puede leer `PAY-TEST-0001.png` desde galeria.

## Publicar A GitHub

En la VPS, dentro de esta carpeta:

```bash
git init
git add .
git commit -m "Initial autopay QR lab"
```

Luego crea un repo en GitHub y empuja:

```bash
git remote add origin https://github.com/TU_USUARIO/autopay-qr-lab.git
git branch -M main
git push -u origin main
```

Si usas GitHub CLI:

```bash
./scripts/publish_to_github.sh autopay-qr-lab private
```
