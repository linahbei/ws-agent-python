#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>

#define SEMAPHORE_LOCKED 1
#define SEMAPHORE_UNLOCKED 0
#define SEMAPHORE_TIMEOUT -1
#define DEMO_DEMAPHORE "./semaphores/endpoint1/semaphore"

int wrtie_agent_status(char *semaphore_file, int status);
int read_agent_status(char *semaphore_file);
int is_agent_busy(char *semaphore_file);
void call_agent(char *semaphore_file);
void print_datetime_log(char *msg);
void call_example();

int main() {
    // Loop stress testing of WS Agent 
    while(1) {
        call_example();
        // Go to next round testing
        sleep(1);
    }
    return 0;
}

void call_example() {
    char msg[256];
    int status, first_running = 1;
    
    // Force clean up WS agent status when first running
    if(first_running == 0) {
        wrtie_agent_status(DEMO_DEMAPHORE, SEMAPHORE_UNLOCKED);
        first_running = 0;
    }
    // Waiting for already running agent process
    else if(is_agent_busy(DEMO_DEMAPHORE) == SEMAPHORE_LOCKED)
        print_datetime_log("WS Agent is keep busy");   
    // Begin test
    else {   
        print_datetime_log("Call Agent");
        // Call WS Agent
        call_agent(DEMO_DEMAPHORE);
        while(1) {
            // Waiting for process done
            if((status = read_agent_status(DEMO_DEMAPHORE)) == SEMAPHORE_LOCKED)
                print_datetime_log("WS Agent is keep busy");
            else {
                // Show result from WS Agent
                sprintf(msg, " Agent result : %s (%d)\n", 
                        status == SEMAPHORE_UNLOCKED ? "DONE" :
                            status == SEMAPHORE_TIMEOUT ? "TIMEOUT" : "UNKNOWN",
                        status);
                print_datetime_log(msg);
                break;
            }
            sleep(1);
        }
    }
}

int is_agent_busy(char *semaphore_file) {
    if(access(semaphore_file, F_OK) != 0 ||
        access(semaphore_file, R_OK|W_OK) == 0)
        return SEMAPHORE_UNLOCKED;
    else
        return SEMAPHORE_LOCKED;
}

int read_agent_status(char *semaphore_file) {
    int status;
    FILE* fp = fopen(semaphore_file, "r");
    if(fp == NULL)
        return SEMAPHORE_LOCKED;
    else {
        fscanf(fp, "%d", &status);
        fclose(fp);
        return status;
    }
}

int wrtie_agent_status(char *semaphore_file, int status) {
    FILE* fp = fopen(semaphore_file, "w");
    if(fp == NULL)
        return SEMAPHORE_LOCKED;
    else {
        fprintf(fp, "%d", status);
        fclose(fp);
        return 0;
    }
}

void call_agent(char *semaphore_file) {
    wrtie_agent_status(semaphore_file, SEMAPHORE_LOCKED);
    system("python ./ws_agent.py --env lab --endpoints endpoint1");
}

void print_datetime_log(char *msg) {
    time_t  timer = time(NULL);
    printf("%s %s\n", ctime(&timer), msg);
}