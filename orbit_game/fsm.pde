import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

class FSM {

    State currentState;

    FSM(State initialState) {
        currentState = initialState;
    }

    void update() {
        currentState.executeFunction();
    }

    State getCurrentState(){
        return currentState;
    }

    boolean isInState(State state){
        return currentState == state;
    }

    void transitionTo(State newState) {
        currentState.exitFunction();
        currentState = newState;
        currentState.enterFunction();
    }

}

class State {

    PApplet parent;
    Method enterFunction;
    Method executeFunction;
    Method exitFunction;

    State(PApplet p, String enterFunctionName, String executeFunctionName, String exitFunctionName) {
    
        parent = p;
        Class sketchClass = parent.getClass();
        try { 
            enterFunction = sketchClass.getMethod(enterFunctionName);
            executeFunction = sketchClass.getMethod(executeFunctionName);
            exitFunction = sketchClass.getMethod(exitFunctionName);
        } catch(NoSuchMethodException e) {
            println("One of the state transition function is missing.");
        }

    }

    void enterFunction() {

        try {
            enterFunction.invoke(parent);
        } catch(IllegalAccessException e) {
            println("State enter function is missing or something is wrong with it.");
        } catch(InvocationTargetException e) {
            println("State enter function is missing.");
        }
    
    }

    void executeFunction() {
        
        try {
            executeFunction.invoke(parent);
        } catch(IllegalAccessException e) {
            println("State execute function is missing or something is wrong with it.");
        } catch(InvocationTargetException e) {
            println("State execute function is missing.");
        }

    }

    void exitFunction() {

        try {
            exitFunction.invoke(parent);
        } catch(IllegalAccessException e) {
            println("State exit function is missing or something is wrong with it.");
        } catch(InvocationTargetException e) {
            println("State exit function is missing.");
        }
    
    }

}