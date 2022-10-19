CC = gcc
ARGS = -Wall -O0 -g -I .

all: 
	$(CC) $(ARGS) -o server server.c
	$(CC) $(ARGS) -o client client.c
	$(CC) $(ARGS) -o client_microburst client_microburst.c

clean:
	rm -f *.o server client *~
