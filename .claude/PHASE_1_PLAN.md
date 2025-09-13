# Phase 1: Frontend Foundation Implementation Plan

## Status: ACTIVE
**Started:** December 9, 2024
**Target Completion:** Week 1A (Dec 16, 2024)

---

## 🎯 PHASE 1 GOAL
Build the complete "Single Slate" interface foundation BEFORE connecting to backend, focusing on the Spaces → Flows → Blocks information architecture and core UI components.

---

## 📋 COMPLETED RESEARCH & DESIGN

### ✅ Technical Architecture Research
- **Next.js 14 App Router**: File-system routing perfect for hierarchical structure, parallel routes for sidebar+content
- **BlockNote Editor**: Block-first architecture with extensible custom blocks
- **Zustand + Immer**: Flat normalized state structure following 2025 best practices
- **Radix UI + Tailwind**: Accessible, customizable components

### ✅ Data Structure Design
```typescript
// Flat, normalized structure for performance
interface AppState {
  spaces: Record<string, Space>    // Flat map of all spaces
  flows: Record<string, Flow>      // Flat map of all flows  
  blocks: Record<string, Block>    // Flat map of all blocks
  currentSpaceId: string | null
  currentFlowId: string | null
}

// Hierarchical relationships via IDs
interface Space {
  id: string
  name: string
  flowIds: string[]  // References to flows
}

interface Flow {
  id: string
  spaceId: string    // Parent space reference
  blockIds: string[] // Ordered block references
}

interface Block {
  id: string
  flowId: string         // Parent flow reference
  parentBlockId?: string // For indented sub-flows
  childBlockIds: string[]
  indentLevel: number    // 0, 1, 2, 3+ for visual hierarchy
}
```

### ✅ Route Structure Design
```
app/
├── layout.tsx                    # Root layout
├── page.tsx                      # Dashboard/home
├── spaces/
│   ├── layout.tsx               # Spaces layout with sidebar
│   ├── page.tsx                 # All spaces view
│   └── [spaceId]/
│       ├── layout.tsx           # Space-specific layout
│       ├── page.tsx             # Space overview
│       └── flows/
│           ├── layout.tsx       # Flows layout
│           ├── page.tsx         # All flows in space
│           └── [flowId]/
│               ├── layout.tsx   # Flow editor layout
│               └── page.tsx     # Flow editor with BlockNote
```

---

## 🔄 CURRENT STEP: Human Test Preparation

### IMMEDIATE ACTIONS REQUIRED:

#### 1. Create Frontend Project Structure
```bash
# From composer root directory
npx create-next-app@latest frontend --typescript --tailwind --app

cd frontend

# Add dependencies
npm install zustand @blocknote/core @blocknote/react @blocknote/mantine
npm install @radix-ui/react-navigation-menu @radix-ui/react-dropdown-menu
npm install immer uuid lucide-react

# Create folder structure
mkdir -p app/spaces/[spaceId]/flows/[flowId]
mkdir -p components/ui components/spaces components/flows components/blocks
mkdir -p lib/stores lib/types lib/utils
```

#### 2. Implement Basic Information Architecture
**MUST HAVE for Human Test:**
- Spaces sidebar with collapsible navigation
- Flow list within each space  
- Block editor with basic text blocks
- Navigation between Spaces → Flows → Blocks
- Visual hierarchy with indentation

#### 3. Create Test Data
```typescript
// Test scenario: Marketing Operations space with Weekly Revenue Report flow
const testData = {
  spaces: {
    'marketing-ops': {
      id: 'marketing-ops',
      name: 'Marketing Operations', 
      icon: '📊',
      flowIds: ['weekly-revenue']
    }
  },
  flows: {
    'weekly-revenue': {
      id: 'weekly-revenue',
      name: 'Weekly Revenue Report',
      spaceId: 'marketing-ops',
      blockIds: ['main-task', 'sub-task-1', 'sub-task-2']
    }
  },
  blocks: {
    'main-task': {
      id: 'main-task',
      content: 'Every Monday at 9am, get last week\'s sales data from our CRM',
      indentLevel: 0,
      status: 'ready'
    },
    'sub-task-1': {
      id: 'sub-task-1', 
      content: 'Compare to previous week and calculate percentage change',
      indentLevel: 1,
      parentBlockId: 'main-task',
      status: 'draft'
    },
    'sub-task-2': {
      id: 'sub-task-2',
      content: 'If revenue dropped >10%, send analysis to leadership team',  
      indentLevel: 1,
      parentBlockId: 'main-task',
      status: 'draft'
    }
  }
}
```

---

## 🧪 HUMAN TEST PLAN

### Test 1: Information Architecture Validation
**Goal:** Validate that Spaces → Flows → Blocks feels natural

**Method:**
1. Show user the sidebar navigation
2. Ask: "Create a new space called 'Sales Operations'"  
3. Ask: "Add a flow called 'Customer Onboarding'"
4. Ask: "Add blocks for each onboarding step"
5. Observe navigation patterns and confusion points

**Success Criteria:**
- User understands hierarchy immediately
- Navigation feels intuitive  
- User can return to previous items easily
- No questions about "where am I?" or "how do I get back?"

### Test 2: Block Creation & Hierarchy
**Goal:** Validate that writing workflows with indentation feels natural

**Method:**
1. Start with empty flow
2. Ask: "Describe your morning standup automation in blocks"
3. Watch them create main tasks and sub-tasks
4. Test indentation with Tab/Shift+Tab
5. Test drag & drop reordering

**Success Criteria:**  
- User writes naturally without technical syntax
- Indentation for sub-tasks feels obvious
- Block creation is effortless
- Visual hierarchy matches mental model

### Test 3: Block States & Visual Feedback  
**Goal:** Validate that block statuses are clear and actionable

**Method:**
1. Show blocks in different states (draft, ready, completed)
2. Ask: "What do you expect each status to mean?"
3. Ask: "What would happen if you clicked this ▶️ button?"
4. Test expandable results interface

**Success Criteria:**
- User immediately understands each state
- Run affordances feel safe and clickable
- Visual feedback is clear and informative

---

## 📋 NEXT STEPS AFTER HUMAN TEST

### Phase 1B: Core Workflow Experience (Week 1B)
**Requirements from Phase 1A:**
1. **Validated Information Architecture**: Spaces → Flows → Blocks navigation must be intuitive
2. **Working Block Editor**: Users can create, edit, and organize blocks naturally
3. **Visual Hierarchy System**: Indentation and nesting must feel natural
4. **Block State Management**: Clear visual feedback for different block states

**Phase 1B Will Add:**
1. **Backend Connection**: Connect to existing `/v1/tasks` API
2. **Intent Recognition**: Parse natural language into executable plans
3. **Inline Execution**: Show results where intent was written
4. **Real-time Feedback**: Status updates during execution

### Phase 1C: @-Mention System (End of Week 1)
**Requirements from Phase 1B:**
1. **Working Execution Flow**: Blocks can be sent to backend and return results
2. **Stable Editor Integration**: BlockNote customization proven to work
3. **State Management Patterns**: Zustand store handling complex updates smoothly

**Phase 1C Will Add:**
1. **@-Mention Autocomplete**: Smart chip interface for tools
2. **Tool Discovery**: Connect to existing tool registry 
3. **Chip State Management**: Connected/disconnected/loading states

---

## ⚠️ CRITICAL SUCCESS FACTORS

### Must Work Before Moving Forward:
1. **Navigation feels instant and obvious** - no confusion about hierarchy
2. **Writing blocks feels like writing** - not like using software
3. **Visual hierarchy is clear** - indentation conveys meaning immediately
4. **State is persistent** - refreshing page doesn't lose work

### Technical Debt to Avoid:
1. **Deep nesting in state** - keep flat structure from day 1
2. **Tight coupling** - components should work independently  
3. **Performance issues** - use atomic selectors and avoid unnecessary re-renders
4. **Accessibility gaps** - keyboard navigation must work perfectly

---

## 📊 SUCCESS METRICS

### Qualitative (Human Test):
- "This feels like Notion but it actually does things"
- "I immediately understood how to organize my workflows"  
- "The hierarchy makes perfect sense"
- "I want to start using this for real work"

### Quantitative (After Implementation):
- Navigation time: Space → Flow → Block < 3 clicks
- Block creation time: < 10 seconds from thought to text
- Page load time: < 2 seconds on desktop
- Zero JavaScript errors in console

---

## 🚀 READY TO PROCEED

**NEXT ACTION:** Create frontend project and implement basic information architecture for human testing.

**ESTIMATED TIME:** 2 days to basic clickable prototype + 1 day human testing + iterations

**DECISION POINT:** After human test validation, proceed to Phase 1B (backend connection) or iterate on information architecture based on feedback.

---

*Updated: December 9, 2024*
*Status: Research complete, implementation ready to begin*