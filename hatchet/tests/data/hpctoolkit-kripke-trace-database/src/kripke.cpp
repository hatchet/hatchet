//
// Copyright (c) 2014-19, Lawrence Livermore National Security, LLC
// and Kripke project contributors. See the COPYRIGHT file for details.
//
// SPDX-License-Identifier: (BSD-3-Clause)
//

#include <Kripke.h>
#include <Kripke/Core/Comm.h>
#include <Kripke/Core/DataStore.h>
#include <Kripke/Core/Set.h>
#include <Kripke/ArchLayout.h>
#include <Kripke/Generate.h>
#include <Kripke/InputVariables.h>
#include <Kripke/SteadyStateSolver.h>
#include <Kripke/Timing.h>
#include <stdio.h>
#include <string.h>
#include <algorithm>
#include <string>
#include <sstream>

#ifdef KRIPKE_USE_OPENMP
#include <omp.h>
#endif

#ifdef KRIPKE_USE_CALIPER
#include <caliper/cali.h>
#endif

#ifdef __bgq__
#include </bgsys/drivers/ppcfloor/spi/include/kernel/location.h>
#endif



void usage(void){

  Kripke::Core::Comm comm;
  if(comm.rank() == 0){
    // Get a new object with defaulted values
    InputVariables def;

    // Display command line
    printf("Usage:  [srun ...] kripke [options...]\n\n");

    // Display each option
    printf("Problem Size Options:\n");
    printf("---------------------\n");

    printf("  --groups <ngroups>     Number of energy groups\n");
    printf("                         Default:  --groups %d\n\n", def.num_groups);

    printf("  --legendre <lorder>    Scattering Legendre Expansion Order (0, 1, ...)\n");
    printf("                         Default:  --legendre %d\n\n", def.legendre_order);

    printf("  --quad [<ndirs>|<polar>:<azim>]\n");
    printf("                         Define the quadrature set to use\n");
    printf("                         Either a fake S2 with <ndirs> points,\n");
    printf("                         OR Gauss-Legendre with <polar> by <azim> points\n");
    printf("                         Default:  --quad %d\n\n", def.num_directions);



    printf("  --zones <x,y,z>        Number of zones in x,y,z\n");
    printf("                         Default:  --zones %d,%d,%d\n\n", def.nx, def.ny, def.nz);


    printf("\n");
    printf("Physics Parameters:\n");
    printf("-------------------\n");
    printf("  --sigt <st0,st1,st2>   Total material cross-sections\n");
    printf("                         Default:   --sigt %lf,%lf,%lf\n\n", def.sigt[0], def.sigt[1], def.sigt[2]);

    printf("  --sigs <ss0,ss1,ss2>   Scattering material cross-sections\n");
    printf("                         Default:   --sigs %lf,%lf,%lf\n\n", def.sigs[0], def.sigs[1], def.sigs[2]);


    printf("\n");
    printf("On-Node Options:\n");
    printf("----------------\n");
    printf("  --arch <ARCH>          Architecture selection\n");
    printf("                         Available: Sequential, OpenMP, CUDA\n");
    printf("                         Default:   --arch %s\n\n", archToString(def.al_v.arch_v).c_str());
    printf("  --layout <LAYOUT>      Data layout and loop nesting order\n");
    printf("                         Available: DGZ,DZG,GDZ,GZD,ZDG,ZGD\n");
    printf("                         Default:   --layout %s\n\n", layoutToString(def.al_v.layout_v).c_str());

    printf("\n");
    printf("Parallel Decomposition Options:\n");
    printf("-------------------------------\n");

    printf("  --procs <npx,npy,npz>  Number of MPI ranks in each spatial dimension\n");
    printf("                         Default:  --procs %d,%d,%d\n\n", def.npx, def.npy, def.npz);

    printf("  --dset <ds>            Number of direction-sets\n");
    printf("                         Must be a factor of 8, and divide evenly the number\n");
    printf("                         of quadrature points\n");
    printf("                         Default:  --dset %d\n\n", def.num_dirsets);

    printf("  --gset <gs>            Number of energy group-sets\n");
    printf("                         Must divide evenly the number energy groups\n");
    printf("                         Default:  --gset %d\n\n", def.num_groupsets);

    printf("  --zset <zx>,<zy>,<zz>  Number of zone-sets in x,y, and z\n");
    printf("                         Default:  --zset %d,%d,%d\n\n", def.num_zonesets_dim[0], def.num_zonesets_dim[1], def.num_zonesets_dim[2]);

    printf("\n");
    printf("Solver Options:\n");
    printf("---------------\n");

    printf("  --niter <NITER>        Number of solver iterations to run\n");
    printf("                         Default:  --niter %d\n\n", def.niter);

    printf("  --pmethod <method>     Parallel solver method\n");
    printf("                         sweep: Full up-wind sweep (wavefront algorithm)\n");
    printf("                         bj: Block Jacobi\n");
    printf("                         Default: --pmethod sweep\n\n");

    printf("\n");
  }

  Kripke::Core::Comm::finalize();

  exit(1);
}

struct CmdLine {
  CmdLine(int argc, char **argv) :
    size(argc-1),
    cur(0),
    args()
  {
    for(int i = 0;i < size;++ i){
      args.push_back(argv[i+1]);
    }
  }

  std::string pop(void){
    if(atEnd())
      usage();
    return args[cur++];
  }

  bool atEnd(void){
    return(cur >= size);
  }

  int size;
  int cur;
  std::vector<std::string> args;
};

std::vector<std::string> split(std::string const &str, char delim){
  std::vector<std::string> elem;
  std::stringstream ss(str);
  std::string e;
  while(std::getline(ss, e, delim)){
    elem.push_back(e);
  }
  return elem;
}


namespace {
  template<typename T>
  std::string toString(T const &val){
    std::stringstream ss;
    ss << val;
    return ss.str();
  }
}

int main(int argc, char **argv) {
  /*
   * Initialize MPI
   */
  Kripke::Core::Comm::init(&argc, &argv);

  Kripke::Core::Comm comm;

  int myid = comm.rank();
  int num_tasks = comm.size();

  if (myid == 0) {
    /* Print out a banner message along with a version number. */
    printf("\n");
    printf("   _  __       _         _\n");
    printf("  | |/ /      (_)       | |\n");
    printf("  | ' /  _ __  _  _ __  | | __ ___\n");
    printf("  |  <  | '__|| || '_ \\ | |/ // _ \\ \n");
    printf("  | . \\ | |   | || |_) ||   <|  __/\n");
    printf("  |_|\\_\\|_|   |_|| .__/ |_|\\_\\\\___|\n");
    printf("                 | |\n");
    printf("                 |_|        Version %s\n", KRIPKE_VERSION);
    printf("\n");
    printf("LLNL-CODE-775068\n");
    printf("\n");
    printf("Copyright (c) 2014-2019, Lawrence Livermore National Security, LLC\n");
    printf("\n");
    printf("Kripke is released under the BSD 3-Clause License, please see the\n");
    printf("LICENSE file for the full license\n");
    printf("\n");
    printf("This work was produced under the auspices of the U.S. Department of\n");
    printf("Energy by Lawrence Livermore National Laboratory under Contract\n");
    printf("DE-AC52-07NA27344.\n");
    printf("\n");
    printf("Author: Adam J. Kunen <kunen1@llnl.gov>\n");
    printf("\n");

    // Display information about how we were built
    printf("Compilation Options:\n");
    printf("  Architecture:           %s\n", KRIPKE_ARCH);
    printf("  Compiler:               %s\n", KRIPKE_CXX_COMPILER);
    printf("  Compiler Flags:         \"%s\"\n", KRIPKE_CXX_FLAGS);
    printf("  Linker Flags:           \"%s\"\n", KRIPKE_LINK_FLAGS);

#ifdef KRIPKE_USE_CHAI
    printf("  CHAI Enabled:           Yes\n");
#else
    printf("  CHAI Enabled:           No\n");
#endif

#ifdef KRIPKE_USE_CUDA
    printf("  CUDA Enabled:           Yes\n");
    printf("    NVCC:                 %s\n", KRIPKE_NVCC_COMPILER);
    printf("    NVCC Flags:           \"%s\"\n", KRIPKE_NVCC_FLAGS);
#else
    printf("  CUDA Enabled:           No\n");
#endif

#ifdef KRIPKE_USE_MPI
    printf("  MPI Enabled:            Yes\n");
#else
    printf("  MPI Enabled:            No\n");
#endif

#ifdef KRIPKE_USE_OPENMP
    printf("  OpenMP Enabled:         Yes\n");
#else
    printf("  OpenMP Enabled:         No\n");
#endif

#ifdef KRIPKE_USE_CALIPER
    printf("  Caliper Enabled:        Yes\n");
#else
    printf("  Caliper Enabled:        No\n");
#endif




    /* Print out some information about how OpenMP threads are being mapped
     * to CPU cores.
     */
#ifdef KRIPKE_USE_OPENMP

    // Get max number of threads
    int max_threads = omp_get_max_threads();

    // Allocate an array to store which core each thread is running on
    std::vector<int> thread_to_core(max_threads, -1);

    // Collect thread->core mapping
#pragma omp parallel
    {
      int tid = omp_get_thread_num();
#ifdef __bgq__
      int core = Kernel_ProcessorCoreID();
#else
      int core = sched_getcpu();
#endif
      thread_to_core[tid] = core;
    }

    printf("\nOpenMP Thread->Core mapping for %d threads on rank 0", max_threads);
    for(int tid = 0;tid < max_threads;++ tid){
      if(!(tid%8)){
        printf("\n");
      }
      printf("  %3d->%3d", tid, thread_to_core[tid]);
    }
    printf("\n");
#endif
  }

  /*
   * Default input parameters
   */
  InputVariables vars;

  /*
   * Parse command line
   */
  CmdLine cmd(argc, argv);
  while(!cmd.atEnd()){
    std::string opt = cmd.pop();
    if(opt == "-h" || opt == "--help"){usage();}
    else if(opt == "--name"){vars.run_name = cmd.pop();}
    else if(opt == "--dset"){
      vars.num_dirsets = std::atoi(cmd.pop().c_str());
    }
    else if(opt == "--gset"){
      vars.num_groupsets = std::atoi(cmd.pop().c_str());
    }
    else if(opt == "--zset"){
      std::vector<std::string> nz = split(cmd.pop(), ',');
      if(nz.size() != 3) usage();
      vars.num_zonesets_dim[0] = std::atoi(nz[0].c_str());
      vars.num_zonesets_dim[1] = std::atoi(nz[1].c_str());
      vars.num_zonesets_dim[2] = std::atoi(nz[2].c_str());
    }
    else if(opt == "--zones"){
      std::vector<std::string> nz = split(cmd.pop(), ',');
      if(nz.size() != 3) usage();
      vars.nx = std::atoi(nz[0].c_str());
      vars.ny = std::atoi(nz[1].c_str());
      vars.nz = std::atoi(nz[2].c_str());
    }
    else if(opt == "--procs"){
      std::vector<std::string> np = split(cmd.pop(), ',');
      if(np.size() != 3) usage();
      vars.npx = std::atoi(np[0].c_str());
      vars.npy = std::atoi(np[1].c_str());
      vars.npz = std::atoi(np[2].c_str());
    }
    else if(opt == "--pmethod"){
      std::string method = cmd.pop();
      if(!strcasecmp(method.c_str(), "sweep")){
        vars.parallel_method = PMETHOD_SWEEP;
      }
      else if(!strcasecmp(method.c_str(), "bj")){
        vars.parallel_method = PMETHOD_BJ;
      }
      else{
        usage();
      }
    }
    else if(opt == "--groups"){
      vars.num_groups = std::atoi(cmd.pop().c_str());
    }
    else if(opt == "--quad"){
      std::vector<std::string> p = split(cmd.pop(), ':');
      if(p.size() == 1){
        vars.num_directions = std::atoi(p[0].c_str());
        vars.quad_num_polar = 0;
        vars.quad_num_azimuthal = 0;
      }
      else if(p.size() == 2){
        vars.quad_num_polar = std::atoi(p[0].c_str());
        vars.quad_num_azimuthal = std::atoi(p[1].c_str());
        vars.num_directions = vars.quad_num_polar * vars.quad_num_azimuthal;
      }
      else{
        usage();
      }
    }
    else if(opt == "--legendre"){
      vars.legendre_order = std::atoi(cmd.pop().c_str());
    }
    else if(opt == "--sigs"){
      std::vector<std::string> values = split(cmd.pop(), ',');
      if(values.size()!=3)usage();
      for(int mat = 0;mat < 3;++ mat){
        vars.sigs[mat] = std::atof(values[mat].c_str());
      }
    }
    else if(opt == "--sigt"){
      std::vector<std::string> values = split(cmd.pop(), ',');
      if(values.size()!=3)usage();
      for(int mat = 0;mat < 3;++ mat){
        vars.sigt[mat] = std::atof(values[mat].c_str());
      }
    }
    else if(opt == "--niter"){
      vars.niter = std::atoi(cmd.pop().c_str());
    }
    else if(opt == "--arch"){
      vars.al_v.arch_v = Kripke::stringToArch(cmd.pop());
    }
    else if(opt == "--layout"){
      vars.al_v.layout_v = Kripke::stringToLayout(cmd.pop());
    }
    else{
      printf("Unknwon options %s\n", opt.c_str());
      usage();
    }
  }

  // Check that the input arguments are valid
  if(vars.checkValues()){
    exit(1);
  }

  /*
   * Display Options
   */
  if (myid == 0) {

    printf("\nInput Parameters\n");
    printf("================\n");

    printf("\n");
    printf("  Problem Size:\n");
    printf("    Zones:                 %d x %d x %d  (%d total)\n", vars.nx, vars.ny, vars.nz, vars.nx*vars.ny*vars.nz);
    printf("    Groups:                %d\n", vars.num_groups);
    printf("    Legendre Order:        %d\n", vars.legendre_order);
    printf("    Quadrature Set:        ");
    if(vars.quad_num_polar == 0){
      printf("Dummy S2 with %d points\n", vars.num_directions);
    }
    else {
      printf("Gauss-Legendre, %d polar, %d azimuthal (%d points)\n", vars.quad_num_polar, vars.quad_num_azimuthal, vars.num_directions);
    }


    printf("\n");
    printf("  Physical Properties:\n");
    printf("    Total X-Sec:           sigt=[%lf, %lf, %lf]\n", vars.sigt[0], vars.sigt[1], vars.sigt[2]);
    printf("    Scattering X-Sec:      sigs=[%lf, %lf, %lf]\n", vars.sigs[0], vars.sigs[1], vars.sigs[2]);


    printf("\n");
    printf("  Solver Options:\n");
    printf("    Number iterations:     %d\n", vars.niter);



    printf("\n");
    printf("  MPI Decomposition Options:\n");
    printf("    Total MPI tasks:       %d\n", num_tasks);
    printf("    Spatial decomp:        %d x %d x %d MPI tasks\n", vars.npx, vars.npy, vars.npz);
    printf("    Block solve method:    ");
    if(vars.parallel_method == PMETHOD_SWEEP){
      printf("Sweep\n");
    }
    else if(vars.parallel_method == PMETHOD_BJ){
      printf("Block Jacobi\n");
    }


    printf("\n");
    printf("  Per-Task Options:\n");
    printf("    DirSets/Directions:    %d sets, %d directions/set\n", vars.num_dirsets, vars.num_directions/vars.num_dirsets);
    printf("    GroupSet/Groups:       %d sets, %d groups/set\n", vars.num_groupsets, vars.num_groups/vars.num_groupsets);
    printf("    Zone Sets:             %d x %d x %d\n", vars.num_zonesets_dim[0], vars.num_zonesets_dim[1], vars.num_zonesets_dim[2]);
    printf("    Architecture:          %s\n", archToString(vars.al_v.arch_v).c_str());
    printf("    Data Layout:           %s\n", layoutToString(vars.al_v.layout_v).c_str());




  }

  /*
   * Set Caliper globals
   */

#ifdef KRIPKE_USE_CALIPER
  cali_set_global_int_byname("kripke.nx", vars.nx);
  cali_set_global_int_byname("kripke.ny", vars.ny);
  cali_set_global_int_byname("kripke.nz", vars.nz);

  cali_set_global_int_byname("kripke.groups",         vars.num_groups);
  cali_set_global_int_byname("kripke.legendre_order", vars.legendre_order);

  if (vars.parallel_method == PMETHOD_SWEEP)
      cali_set_global_string_byname("kripke.parallel_method", "sweep");
  else if (vars.parallel_method == PMETHOD_BJ)
      cali_set_global_string_byname("kripke.parallel_method", "block jacobi");

  cali_set_global_string_byname("kripke.architecture", archToString(vars.al_v.arch_v).c_str());
  cali_set_global_string_byname("kripke.layout", layoutToString(vars.al_v.layout_v).c_str());
#endif

  // Allocate problem

  Kripke::Core::DataStore data_store;
  Kripke::generateProblem(data_store, vars);

  // Run the solver
  Kripke::SteadyStateSolver(data_store, vars.niter, vars.parallel_method == PMETHOD_BJ);

  // Print Timing Info
  auto &timing = data_store.getVariable<Kripke::Timing>("timing");
  timing.print();

  // Compute performance metrics
  auto &set_group  = data_store.getVariable<Kripke::Core::Set>("Set/Group");
  auto &set_dir    = data_store.getVariable<Kripke::Core::Set>("Set/Direction");
  auto &set_zone   = data_store.getVariable<Kripke::Core::Set>("Set/Zone");

  size_t num_unknowns = set_group.globalSize()
                      * set_dir.globalSize()
                      * set_zone.globalSize();

  size_t num_iter = timing.getCount("SweepSolver");
  double solve_time = timing.getTotal("Solve");
  double iter_time = solve_time / num_iter;
  double grind_time = iter_time / num_unknowns;
  double throughput = num_unknowns / iter_time;

  double sweep_eff = 100.0 * timing.getTotal("SweepSubdomain") / timing.getTotal("SweepSolver");

  if(myid == 0){
    printf("\n");
    printf("Figures of Merit\n");
    printf("================\n");
    printf("\n");
    printf("  Throughput:         %e [unknowns/(second/iteration)]\n", throughput);
    printf("  Grind time :        %e [(seconds/iteration)/unknowns]\n", grind_time);
    printf("  Sweep efficiency :  %4.5lf [100.0 * SweepSubdomain time / SweepSolver time]\n", sweep_eff);
    printf("  Number of unknowns: %lu\n", (unsigned long) num_unknowns);
  }

  // Cleanup and exit
  Kripke::Core::Comm::finalize();

  if(myid == 0){
    printf("\n");
    printf("END\n");
  }
  return (0);
}
