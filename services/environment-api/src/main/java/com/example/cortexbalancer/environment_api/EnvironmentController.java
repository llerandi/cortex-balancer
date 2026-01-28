package com.example.cortexbalancer.environment_api;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/environment")
public class EnvironmentController {

    // A logger to see what is happening on the console
    private static final Logger log = LoggerFactory.getLogger(EnvironmentController.class);

    /**
     * Endpoint to restart the environment
     * The AI will call it at the beginning of each training 'episode'
     *
     * @return the initial state of the system
     */
    @GetMapping("/reset")
    public ApiDto.ResetResponse resetEnvironment() {
        log.info("-> GET /reset: Resetting the environment to an initial state.");

        // TODO: logic
        // For testing, return a fixed initial state
        List<Double> initialState = List.of(0.0, 0.0, 0.0);

        return new ApiDto.ResetResponse(initialState);
    }

    /**
     * Endpoint to execute a step in the environment
     * The AI will send the action it has decided to take
     *
     * @param request body of the request (contains the action)
     * @return new state, reward, and whether the episode has ended
     */
    @PostMapping("/step")
    public ApiDto.StepResponse step(@RequestBody ApiDto.ActionRequest request) {
        log.info("-> POST /step: Action received = {}", request.action());

        /**
         * TODO: logic
         * 1. Call the corresponding worker (e.g., worker-2 if action() is 2)
         * 2. Measure the response latency
         * 3. Calculate a reward based on latency
         * 4. Calculate the new actual state of the system
         */

        // For testing, return fixed values to test the communication
        double reward = 1.0; // A positive fixed reward
        List<Double> newState = List.of(0.1, 0.5, 0.2); // A fictitious state
        boolean isDone = false; // The episode never ends

        log.info("<- Returning: newState={}, reward={}, done={}", newState, reward, isDone);

        return new ApiDto.StepResponse(newState, reward, isDone);
    }
}