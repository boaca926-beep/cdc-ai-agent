up-gpu:
	docker compose -f docker-compose.yml -f docker-compose.override.yml \
	               -f docker-compose.gpu.yml up -d

up-cpu:
	docker compose -f docker-compose.yml -f docker-compose.override.yml \
	               -f docker-compose.cpu.yml up -d

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f

rebuild:
	docker compose -f docker-compose.yml -f docker-compose.override.yml \
                   -f docker-compose.gpu.yml up -d --build