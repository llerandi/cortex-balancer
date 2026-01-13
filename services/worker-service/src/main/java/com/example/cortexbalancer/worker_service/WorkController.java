package com.example.cortexbalancer.worker_service;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.concurrent.ThreadLocalRandom;

@RestController
public class WorkController {

    /**
     * This endpoint simulates a workload.
     *
     * * Upon receiving a POST request to /work, it pauses for a random amount of time,
     * * and then responds indicating how long it took and which worker (container) processed the request
     */
    @PostMapping("/work")
    public String doWork() throws InterruptedException {
        // Simulate a workload with a random duration (between 200 and 800 ms)
        long workTime = ThreadLocalRandom.current().nextLong(200, 800);
        Thread.sleep(workTime);

        // Obtains the host/container name to find out which worker responded
        String hostName = getHostName();

        // Returns an informative response
        return String.format("Work completed in %d ms by worker: %s", workTime, hostName);
    }

    /**
     * Method to obtain the hostname of the container
     *
     * * This will be crucial later on to verify that the balancer distributes the load between different instances
     */
    private String getHostName() {
        try {
            // Attempts to obtain the hostname of the OS or container
            return InetAddress.getLocalHost().getHostName();
        } catch (UnknownHostException e) {
            // In the event of an error, return a generic name
            return "unknown-worker";
        }
    }
}