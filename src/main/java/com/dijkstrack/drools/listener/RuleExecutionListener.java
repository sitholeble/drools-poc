package com.dijkstrack.drools.listener;

import org.kie.api.event.rule.*;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * Listener to track rule execution events for audit and debugging purposes.
 * Captures which rules fired, when they fired, and what facts triggered them.
 */
public class RuleExecutionListener implements AgendaEventListener, RuleRuntimeEventListener {
    
    private final List<RuleExecutionEvent> executionHistory = new CopyOnWriteArrayList<>();
    private final List<String> firedRules = new ArrayList<>();
    
    @Override
    public void matchCreated(MatchCreatedEvent event) {
        String ruleName = event.getMatch().getRule().getName();
        RuleExecutionEvent executionEvent = new RuleExecutionEvent(
            ruleName,
            "MATCHED",
            System.currentTimeMillis(),
            event.getMatch().getObjects().toString()
        );
        executionHistory.add(executionEvent);
        System.out.println("[DROOLS] Rule matched: " + ruleName);
    }
    
    @Override
    public void matchCancelled(MatchCancelledEvent event) {
        String ruleName = event.getMatch().getRule().getName();
        System.out.println("[DROOLS] Rule cancelled: " + ruleName);
    }
    
    @Override
    public void beforeMatchFired(BeforeMatchFiredEvent event) {
        String ruleName = event.getMatch().getRule().getName();
        System.out.println("[DROOLS] Before firing: " + ruleName);
    }
    
    @Override
    public void afterMatchFired(AfterMatchFiredEvent event) {
        String ruleName = event.getMatch().getRule().getName();
        firedRules.add(ruleName);
        
        RuleExecutionEvent executionEvent = new RuleExecutionEvent(
            ruleName,
            "FIRED",
            System.currentTimeMillis(),
            event.getMatch().getObjects().toString()
        );
        executionHistory.add(executionEvent);
        
        System.out.println("[DROOLS] After firing: " + ruleName + 
                          " | Facts: " + event.getMatch().getObjects().size());
    }
    
    @Override
    public void agendaGroupPopped(AgendaGroupPoppedEvent event) {
        System.out.println("[DROOLS] Agenda group popped: " + event.getAgendaGroup());
    }
    
    @Override
    public void agendaGroupPushed(AgendaGroupPushedEvent event) {
        System.out.println("[DROOLS] Agenda group pushed: " + event.getAgendaGroup());
    }
    
    @Override
    public void beforeRuleFlowGroupActivated(RuleFlowGroupActivatedEvent event) {
        System.out.println("[DROOLS] Rule flow group activated: " + event.getRuleFlowGroup());
    }
    
    @Override
    public void afterRuleFlowGroupActivated(RuleFlowGroupActivatedEvent event) {
        // No-op
    }
    
    @Override
    public void beforeRuleFlowGroupDeactivated(RuleFlowGroupDeactivatedEvent event) {
        System.out.println("[DROOLS] Rule flow group deactivated: " + event.getRuleFlowGroup());
    }
    
    @Override
    public void afterRuleFlowGroupDeactivated(RuleFlowGroupDeactivatedEvent event) {
        // No-op
    }
    
    @Override
    public void objectInserted(ObjectInsertedEvent event) {
        String factType = event.getObject().getClass().getSimpleName();
        System.out.println("[DROOLS] Fact inserted: " + factType);
    }
    
    @Override
    public void objectUpdated(ObjectUpdatedEvent event) {
        String factType = event.getObject().getClass().getSimpleName();
        System.out.println("[DROOLS] Fact updated: " + factType);
    }
    
    @Override
    public void objectDeleted(ObjectDeletedEvent event) {
        String factType = event.getObject().getClass().getSimpleName();
        System.out.println("[DROOLS] Fact deleted: " + factType);
    }
    
    /**
     * Get complete execution history
     */
    public List<RuleExecutionEvent> getExecutionHistory() {
        return new ArrayList<>(executionHistory);
    }
    
    /**
     * Get list of fired rule names
     */
    public List<String> getFiredRules() {
        return new ArrayList<>(firedRules);
    }
    
    /**
     * Get count of fired rules
     */
    public int getFiredRuleCount() {
        return firedRules.size();
    }
    
    /**
     * Clear execution history
     */
    public void clearHistory() {
        executionHistory.clear();
        firedRules.clear();
    }
    
    /**
     * Inner class to represent a rule execution event
     */
    public static class RuleExecutionEvent {
        private final String ruleName;
        private final String eventType;
        private final long timestamp;
        private final String facts;
        
        public RuleExecutionEvent(String ruleName, String eventType, long timestamp, String facts) {
            this.ruleName = ruleName;
            this.eventType = eventType;
            this.timestamp = timestamp;
            this.facts = facts;
        }
        
        public String getRuleName() {
            return ruleName;
        }
        
        public String getEventType() {
            return eventType;
        }
        
        public long getTimestamp() {
            return timestamp;
        }
        
        public String getFacts() {
            return facts;
        }
        
        @Override
        public String toString() {
            return String.format("RuleExecutionEvent{rule='%s', type='%s', time=%d, facts='%s'}", 
                ruleName, eventType, timestamp, facts);
        }
    }
}

