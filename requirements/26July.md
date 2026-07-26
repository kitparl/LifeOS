# Enterprise Task Management System Redesign Prompt



You are a **Senior Software Architect**, **Senior Backend Engineer**, and **Senior Full-Stack Engineer**.



I already have a working **Task Module**. Your job is **NOT** to rebuild it from scratch. Instead, redesign and extend the existing module into an **enterprise-grade Task Management System** comparable to **ClickUp, Jira, Asana, Linear, and Notion**, while maintaining **backward compatibility** with the current implementation.



## Primary Objective



Create a scalable, production-ready architecture that supports future growth without breaking existing functionality.



The implementation must follow:



* Clean Architecture

* SOLID Principles

* Domain-Driven Design where appropriate

* Repository Pattern

* Service Layer

* DTOs

* Request Validation

* Database Transactions

* Domain Events

* Proper Exception Handling

* API Documentation

* Unit & Integration Tests

* Database Migrations & Seeders

* Database Normalization (3NF or better)

* Soft Deletes where appropriate

* Optimized Indexes

* Pagination

* Lazy Loading

* Caching where beneficial



Avoid duplicated logic. Keep the code modular, maintainable, and extensible.



---



# Source of Truth



The application database is always the **single source of truth**.



External systems (Telegram, Email, Push Notifications, etc.) are only communication channels.



If any external integration fails, the business operation must still succeed.



---



# Existing Module



Assume the Task Module already exists.



Before implementing any feature:



1. Analyse the existing architecture.

2. Reuse existing models, services, and APIs whenever possible.

3. Refactor only when necessary.

4. Preserve backward compatibility.

5. Avoid breaking API contracts unless absolutely required.



---



# Implementation Strategy



Do **NOT** generate everything in one step.



Instead, work feature-by-feature in this order:



1. Analyse current module

2. Identify required changes

3. Design database

4. Design domain models

5. Design services

6. Design repositories

7. Design APIs

8. Implement backend

9. Implement validation

10. Implement events

11. Implement notifications

12. Implement tests

13. Update API documentation



For every feature, explain:



* Why the design was chosen

* Database changes

* Migration changes

* API changes

* Business rules

* Edge cases

* Security considerations

* Performance considerations



---



# Business Rules



The attached specification defines all functional requirements.



Implement **every section** exactly as specified unless doing so would violate software engineering best practices.



Where improvements are possible, propose them first before implementation.



---



# Critical Architectural Rules



## Task Status



Task Status is independent from Assignment Status.



Supported Task Status:



* In Progress

* Hold

* Delayed

* Done



Maintain complete status history:



* Previous Status

* New Status

* Changed By

* Timestamp

* Optional Reason



Never mix Task Status with Assignment Status.



---



## Assignment Status



Supported values:



* Pending

* Accepted

* Rejected

* Cancelled

* Reassigned

* Completed



Assignment history must never be overwritten.



Every assignment creates a new history record.



---



## Ownership



Every task contains:



* Created By

* Assigned By

* Assigned To

* Created At

* Updated At

* Accepted At

* Rejected At

* Completed At



Owner always retains ownership even after assigning the task.



---



## Assignment Rules



## Default Assignment Behaviour



Task assignment is **optional**.



### Default Behaviour



When a user creates a task without selecting an assignee:



* The task is automatically assigned to the creator ("Assign to Me").

* The creator becomes both the **Owner** and the **Current Assignee**.

* Assignment Status is automatically **Accepted**.

* No assignment notification is generated.



This is the default behaviour.



---



### Optional Assignment



During task creation or later, the owner may choose to assign the task to:



* Another user

* Multiple users (future-ready)

* Keep it assigned to themselves



The owner is never required to assign the task to someone else.



---



### Future Multiple Assignees



Although the current UI supports only a single assignee, the backend architecture and database must support multiple assignees in the future.



Examples:



* Task → Me

* Task → Rahul

* Task → Rahul + John + David (future)



Use a dedicated `task_assignments` table rather than storing a single assignee on the `tasks` table.



---



### Subtask Assignment



Subtasks are independent of the parent task assignment.



Example:



Parent Task



* Owner: Alice

* Assigned To: Alice (default)



Subtask 1



* Assigned To: Bob



Subtask 2



* Assigned To: Charlie



Subtask 3



* Assigned To: Alice



Subtask 4



* Assigned To: David



Each subtask maintains its own:



* Assignee(s)

* Assignment Status

* Task Status

* Notes

* Activity Log

* Notifications

* Assignment History



Changing the parent task assignee must **not** automatically change subtask assignees unless the user explicitly requests it.



---



### Ownership Rules



The task creator always remains the **Owner**.



Assigning a task does **not** transfer ownership.



Only the owner can:



* Edit task details

* Delete or archive the task

* Change priority

* Change due date

* Assign or reassign users

* Manage watchers

* Manage tags



Assignees only receive permissions appropriate to their assigned work.



## Multiple Assignees (Future Ready)



Although the current UI supports only **one assignee**, the database architecture must support **multiple assignees** in the future without requiring schema redesign.



Use a dedicated `task_assignments` table instead of storing an assignee directly on the `tasks` table.



---



## Parent Task & Subtask Assignment



A parent task may belong to one user.



Each subtask may be assigned independently to a different user.



Example:



Parent Task



* Owner: Alice

* Assignee: Bob



Subtasks:



* Subtask A → Charlie

* Subtask B → David

* Subtask C → Emma



Subtask assignment is completely independent of the parent task assignment.



Each subtask must have its own:



* Assignment

* Assignment Status

* Status

* History

* Notes

* Notifications

* Activity Log



---



## Notification System



The Notification Module is the primary communication system.



Telegram, Email, and Push Notifications are secondary delivery channels.



Notification failures must never roll back successful business transactions.



---



## Telegram Integration



Telegram is optional.



It must:



* Send notifications

* Trigger backend APIs via action buttons

* Never contain business logic

* Never become the source of truth



Accept and Reject buttons must only call backend APIs.



---



## Activity Log



Every important action must be audited, including:



* Create

* Update

* Assign

* Accept

* Reject

* Reassign

* Status Change

* Priority Change

* Due Date Change

* Notes

* Completion

* Archive

* Delete



Store:



* User

* Action

* Old Value

* New Value

* Timestamp



---



## Security



Implement:



* Role-Based Access Control (RBAC)

* Permission checks on every endpoint

* Request validation

* Authorization policies

* Audit logging

* Database transactions

* Concurrency handling

* Race condition protection



---



## Performance



Design for large-scale production usage.



Include:



* Proper indexing

* Efficient joins

* Pagination

* Lazy loading

* Soft deletes

* Optimized queries

* Future caching support



---



## Future Scalability



The architecture must support future implementation of:



* Multiple Assignees

* Teams

* Projects

* Workspaces

* Kanban Board

* Calendar View

* Timeline View

* Gantt Charts

* Recurring Tasks

* Time Tracking

* AI Task Suggestions

* Email Notifications

* Push Notifications

* Mobile Applications

* Public APIs

* Webhooks



without requiring major architectural changes.



---



# Expected Output



For every feature you implement, provide:



1. Database schema changes

2. ERD updates (if required)

3. Migration scripts

4. Entity relationships

5. Models

6. DTOs

7. Repositories

8. Services

9. Controllers

10. Validation

11. Events

12. Notification flow

13. API endpoints

14. Unit tests

15. Integration tests

16. Edge case handling

17. Performance considerations

18. Security considerations

19. Backward compatibility notes



Do not skip any layer of the architecture.



---



# Attached Specification



Use the attached specification as the functional requirements document and implement **every requirement**, including the additional requirement that:



* The same task architecture must support future multiple assignees.

* A parent task can have one assignee while each subtask can be assigned to different users independently.

* The database and domain model should be designed for this flexibility from day one.



Treat the specification as the functional source of truth and use it to drive implementation.