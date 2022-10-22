/*
 * client.c - A simple connection-based client
 * usage: client <host> <port>
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <sys/time.h>

/*
 * error - wrapper for perror
 */
void error(char *msg) {
	perror(msg);
	exit(0);
}

/**
 * Number of microseconds per second
 */
#define MICRO 1000000
size_t get_latency(int i, const struct timeval *start){
	struct timeval now;
	gettimeofday( &now, NULL );
	size_t latency = (now.tv_sec * MICRO + now.tv_usec) - (start->tv_sec*MICRO + start->tv_usec);

	printf("%d, %ld.%06ld, %ld.%06ld, %ld\n", i, start->tv_sec, start->tv_usec, now.tv_sec, now.tv_usec, latency);
	return latency;
}

int main(int argc, char **argv) {
	int socket_fd, port_number, n, i, nb_burst, data_size, nb_iteration, data_size_to_send;
	long long int delay_us;
	struct sockaddr_in server_addr;
	struct hostent *server;
	char *host_name;
	char buf[1400];
	size_t latencies = 0, buf_size = 1400;
	struct timeval begin_ts, end_ts;
	/* check command line arguments */
	if (argc != 5) {
		fprintf(stderr, "usage: %s <host_name> <port> <nb_burst> <nb_iteration>\n", argv[0]);
		exit(0);
	}
	host_name   = argv[1];
	port_number = atoi( argv[2] );
	nb_burst    = atoi( argv[3] );
	nb_iteration= atoi( argv[4] );

	//buf must be big enough to contain a timeval
	data_size = 2;// sizeof(struct timeval);

	//data_size += 8;  //to get 90
	if( nb_burst > buf_size / data_size ){
		fprintf(stderr, "nb_burst must not be bigger than %ld\n", buf_size / data_size );
		exit( 0 );
	}

	/* socket: create the socket */
	socket_fd = socket(AF_INET, SOCK_STREAM, 0);
	if (socket_fd < 0)
		error("ERROR opening socket");

	/* gethostbyname: get the server's DNS entry */
	server = gethostbyname(host_name);
	if (server == NULL) {
		fprintf(stderr, "ERROR, no such host as %s\n", host_name);
		exit(0);
	}

	/* build the server's Internet address */
	bzero((char*) &server_addr, sizeof(server_addr));
	server_addr.sin_family = AF_INET;
	bcopy((char*) server->h_addr, (char*) &server_addr.sin_addr.s_addr,
			server->h_length);
	server_addr.sin_port = htons(port_number);

	/* connect: create a connection with the server */
	if (connect(socket_fd, (struct sockaddr*) &server_addr, sizeof(server_addr)) < 0)
		error("ERROR connecting");

	bzero(buf, sizeof(buf));

	printf("payload size: %d, max burst: %d\n", data_size, data_size * nb_burst );

	printf("index, start time, end time, latency\n");

	for( i=0; i<nb_iteration; i++){
		gettimeofday( &begin_ts, NULL );
		delay_us = 1*100; //x * 0.1 millisecond
		data_size_to_send = data_size;

		//increase payload to create burst
		if( i % nb_burst == 0 ){
			delay_us *= nb_burst/2;
			data_size_to_send *= nb_burst;
		}

		//store the current date into buf
		/* write: send the message line to the server */
		n = write(socket_fd, buf, data_size_to_send);
		if (n < 0)
			error("ERROR writing to socket");
		/* read: print the server's reply */
		bzero(buf, buf_size);
		n = read(socket_fd, buf, data_size_to_send);
		if (n < 0)
			error("ERROR reading from socket");

		//latencies += get_latency( i,  (struct timeval *) buf );

		gettimeofday( &end_ts, NULL );
		delay_us -= ( end_ts.tv_sec - begin_ts.tv_sec ) * 1000000000 + ( end_ts.tv_usec - begin_ts.tv_usec );

		//printf("sleep %d\n", delay_us);
		if( delay_us > 0 ){
			//max delay = 1/4 RTT which is 20 milliseconds
			if( delay_us > 1000 ){
				delay_us = 1000;
			}
			usleep( delay_us );
		}
	}
	close(socket_fd);
	printf("avg latency: %ld", latencies / nb_iteration );
	return 0;
}

