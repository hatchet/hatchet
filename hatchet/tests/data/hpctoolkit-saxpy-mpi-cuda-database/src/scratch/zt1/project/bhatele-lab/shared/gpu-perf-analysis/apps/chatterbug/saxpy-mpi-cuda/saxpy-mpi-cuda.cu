#include <iostream>
#include <cstdint>
#include <cstdlib>
#include <cstdio>
#include <cuda_runtime.h>
#include <mpi.h>
#include <unistd.h>
//#include "nvToolsExt.h"

__global__ void saxpy(double *z, double *x, double *y, double alpha, int N) {

    int idx = blockDim.x*blockIdx.x + threadIdx.x;
    int stride = blockDim.x * gridDim.x;

    for (int i = idx; i < N; i += stride) {
    //if (idx < N)
        z[i] = alpha*x[i] + y[i];
    }
}

int main(int argc, char *argv[]) {

    double *h_z, *h_x, *h_y;
    double *d_z, *d_x, *d_y;
    double alpha = 1.5;
    int N = 4096;
    int iterations = 2;

    MPI_Init(&argc, &argv);
    int commSize, commRank;
    MPI_Comm_size(MPI_COMM_WORLD, &commSize);
    MPI_Comm_rank(MPI_COMM_WORLD, &commRank);
	
    cudaSetDevice(commRank);

    int c;
    char* endp;
    // parse arguments
    while ((c = getopt (argc, argv, "N:i:h")) != -1) {
        switch (c) {
	    case 'N':
	        N = strtol(optarg, &endp, 10);
		break;
	    case 'i':
	        iterations = strtol(optarg, &endp, 10);
	        break;
	    case  'h':
		printf("-N <problem_size> => default: -N 4096\n");
		printf("-i <number_of_iterations> => default: -i 2\n");
		exit(0);
	        break;
	    case '?':
		printf("Unknown argument. Use -h to see the options.\n");
		exit(1);
		break;
	}
    }
   
    if (commRank == 0) { 
        printf("Number of iterations: %d\n", iterations);
    	printf("Problem size (N): %d\n", N);
    }

    int deviceCount = 0;
    cudaGetDeviceCount(&deviceCount);
    printf("Rank %d - Number of GPUs: %d\n", commRank, deviceCount);

    h_z = new double[N];
    h_x = new double[N];
    h_y = new double[N];
    
    for (int it = 0; it < iterations; it++){
	// initialize
	if (commRank == 0){
	    for (int i = 0; i < N; i += 1) {
                h_x[i] = 5.0;
                h_y[i] = -2.0;
		h_z[i] = 0.0;
	    }
	}
	
	// send the input arrays to the other process.
	if (commRank == 0) {
	    MPI_Send(h_x, N, MPI_DOUBLE, 1, it+0, MPI_COMM_WORLD);
	    MPI_Send(h_y, N, MPI_DOUBLE, 1, it+1, MPI_COMM_WORLD);
	}
	else if (commRank == 1) {
	    MPI_Recv(h_x, N, MPI_DOUBLE, 0, it+0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            MPI_Recv(h_y, N, MPI_DOUBLE, 0, it+1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
	}

	cudaMalloc(&d_z, N*sizeof(double));
	cudaMalloc(&d_y, N*sizeof(double));
	cudaMalloc(&d_x, N*sizeof(double));

	// copy arrays from host to device
	cudaMemcpy(d_x, h_x, N*sizeof(double), cudaMemcpyHostToDevice);
	cudaMemcpy(d_y, h_y, N*sizeof(double), cudaMemcpyHostToDevice);
	
    	int threadsPerBlock = 512;
    	int numBlocks = 2; //N/threadsPerBlock + (N % threadsPerBlock != 0);

	// kernel call
	//nvtxRangePushA("saxpy");
    	saxpy<<<numBlocks, threadsPerBlock>>>(d_z, d_x, d_y, alpha, N);
    	//nvtxRangePop();

	// copy arrays back to the host
	cudaMemcpy(h_z, d_z, N*sizeof(double), cudaMemcpyDeviceToHost);

	// check if the results are correct
        bool success = true; 
	for (size_t i = 0; i < N; i += 1) {
            if (std::abs(h_z[i] - (1.5*5.0-2.0)) > 1E-8) {
                success = false;
	    }
        }
	if (!success) {
            printf("Rank %d => Error: incorrect results! it: %d\n", commRank, it);
	}
        else {
	    printf("Rank %d => Correct results! it: %d\n", commRank, it);
	}

	// send the result to rank 0.
	if (commRank == 1) {
	    MPI_Send(h_z, N, MPI_DOUBLE, 0, it+2, MPI_COMM_WORLD);
	}
	else if (commRank == 0) {
	    MPI_Recv(h_z, N, MPI_DOUBLE, 1, it+2, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
	}
    }

    // cleaning
    delete[] h_x;
    delete[] h_y;
    delete[] h_z;	
    
    cudaFree(d_z);
    cudaFree(d_x);
    cudaFree(d_y);

    MPI_Finalize();
    
    return 0;
}
