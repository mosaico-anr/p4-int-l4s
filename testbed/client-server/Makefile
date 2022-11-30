# This source code is copyrighted by Montimage. It is released under MIT license.
# It is part of the French National Research Agency (ANR) MOSAICO project, under grant No ANR-19-CE25-0012.

CC = gcc
ARGS = -Wall -O0 -g -I .

all: server client

server: server.c
	$(CC) $(ARGS) -o server server.c

client: client.c
	$(CC) $(ARGS) -o client client.c

clean:
	rm -f *.o server client *~
