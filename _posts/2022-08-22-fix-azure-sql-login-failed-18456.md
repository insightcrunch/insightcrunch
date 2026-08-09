---
layout: post
title: "Fix Azure SQL Login Failed Error 18456"
page_title: "Fix Azure SQL Login Failed Error 18456: Read the Error State to Diagnose Bad Password, Missing Login, Firewall, Contained User, and Entra Auth Causes"
date: 2022-08-22
categories: ["Technology"]
tags: ["Azure", "Azure SQL Database", "18456", "Troubleshooting", "Identity", "Cloud Computing"]
excerpt: "Azure SQL login failed error 18456 has distinct causes. Read the error state to localize a bad password, missing login, firewall block, or contained user."
image: "/assets/images/blog/blog-21.webp"
reading_time: 60
author: "alex-cunningham"
last_updated: 2026-08-09
lang: en
---
The message reads the same every time. `Login failed for user '<name>'. (Microsoft SQL Server, Error: 18456)`. You retype the password, you try again, the same line comes back, and the instinct after the third attempt is to assume your fingers are wrong or the credential was rotated out from under you. That instinct is what wastes the afternoon. The Azure SQL login failed error 18456 is not one problem with one fix. It is a single surface symptom sitting on top of at least six structurally different causes, and the error carries a number that tells you which one you are looking at before you touch the password field again. Learning to read that number is the difference between a five minute correction and an hour of guessing.

This article treats 18456 the way a senior engineer treats it during an incident: as a signal to decode rather than a credential to re-enter. You will learn what the error actually means at the protocol level, how the error state narrows six causes down to one, how to confirm each cause with a command instead of a hunch, and how to apply the fix that addresses the real failure. By the end you will be able to look at a state number and a connection string and say, with confidence, "this is a contained user hitting master" or "this is a firewall rule, not a credential," and act accordingly.

![Reading the Azure SQL 18456 error state to diagnose login failures - Insight Crunch](/assets/images/blog/blog-21.webp)

## What Error 18456 Actually Means

Error 18456 is raised by the database engine during the authentication handshake, the moment after a client has opened a network connection and presented an identity but before any query runs. The engine attempted to authenticate the principal named in the connection, and authentication did not succeed. The number 18456 is the engine's generic label for "I refused this login," and on its own it tells you almost nothing beyond that refusal. Everything useful lives in the companion value, the error state, which the engine sets to describe why it refused.

The reason this matters so much on Azure SQL Database specifically is that the platform deliberately hides detail from the outside. A server you run yourself writes a verbose explanation into its own error log, where you can read the precise state and a human-readable reason. Azure SQL is a managed, multi-tenant service, and exposing the exact reason for a failed login to an arbitrary client would hand an attacker a free oracle: try a username, read whether the failure says "no such login" or "wrong password," and you have learned which usernames are valid. To deny that oracle, the service frequently returns a masked, generic state to the connecting client while recording the true state in its own telemetry. So part of diagnosing 18456 on Azure is knowing where the honest signal lives and how to retrieve it, because the client-facing message is intentionally vague.

### What is the difference between error 18456 and the error state?

Error 18456 is the fixed code meaning "login failed." The state is a separate small integer that classifies the reason: a wrong password, a login that does not exist, a database the principal cannot open, or an authentication mode mismatch. The code stays constant across every cause; the state is the field that changes and localizes the fault.

The handshake itself runs in a defined order, and knowing that order tells you which failures even reach the 18456 stage. First the client resolves the server name and opens a TCP connection to the gateway. If that fails, you do not get an 18456 at all; you get a connection timeout or a name-resolution error, because authentication never started. Next the Azure SQL gateway evaluates the server-level firewall against the client IP. A firewall rejection produces its own distinct error, 40615, which reads "Cannot open server requested by the login," not 18456, although engineers routinely file both under the same mental category of "it would not let me in." Only after the network path is open and the firewall has admitted the client does the engine evaluate the credential, and only credential and authorization failures at that final stage produce a true 18456. Holding this sequence in your head saves you from chasing a password when the connection never reached the password check.

Authentication on Azure SQL also splits into two worlds that fail differently. SQL authentication uses a login or user with a password stored and verified by the database. Microsoft Entra authentication, formerly called Azure Active Directory, uses a token issued by the identity platform and validated by the database against a principal you have provisioned. An 18456 from a SQL credential and an 18456 from an Entra token have different root causes and different fixes, and one of the first branches in any diagnosis is deciding which authentication world the failing connection lives in. A server configured for Entra-only authentication will reject a SQL password login outright, and the reverse mismatch produces equally confusing refusals, so the authentication mode of both the connection and the server is part of the signal you read.

## How to Read the Error and Gather the Diagnostic Signal

The single most valuable habit for 18456 is to stop reading the word "failed" and start reading the state. The state number is the engine telling you which of its internal rejection paths fired, and each path maps to a different cause and a different fix. The catch on Azure SQL is that the state you see at the client is often the masked value, so the diagnostic procedure has two layers: read whatever state the client surfaces, then, when that state is the generic one, go to the server-side signal where the real state is recorded.

### Where do I find the real 18456 state on Azure SQL?

When the client shows a generic state, the precise state lives server-side. Query `sys.event_log` or the auditing and diagnostic settings on the logical server, or inspect Azure SQL Auditing output if it is enabled. These sources record the actual rejection reason that the client message deliberately withholds, which is what lets you localize the cause.

A locally installed SQL Server writes the failed login to its error log with a line that names the state explicitly, something close to `Login failed for user 'app'. Reason: Password did not match that for the login provided. [CLIENT: 10.0.0.4]`, and the numeric state appears alongside it. On Azure SQL Database you do not have access to that engine error log, so you reach for the managed equivalents. The `sys.event_log` and `sys.database_connection_stats` system views on the logical server expose connection failures and can be aggregated to show whether failures are clustering around throttling, firewall, or login problems. If you have enabled Azure SQL Auditing to a storage account, a Log Analytics workspace, or Event Hubs, the audit records capture authentication failures with more fidelity than the client ever sees. Setting up that auditing before an incident is one of the highest-leverage preventive steps you can take, because it converts a masked client message into a precise server-side record you can query after the fact.

The client message still carries information even when the state is masked. The exact spelling of the principal name in the message tells you what identity was actually presented, which is frequently different from what the engineer believes they sent. A connection string that falls back to integrated security, a cached credential in a tool, or an environment variable that overrode the expected username will all show up as a surprising name in the 18456 line. Read the name in the message against the name you intended to use; a mismatch there resolves a meaningful share of cases before you look at anything else.

### Why does Azure SQL hide the real reason for a login failure?

Azure SQL masks the detailed state to prevent username enumeration. If the error told every client whether a failure meant "no such login" versus "wrong password," an attacker could probe valid usernames cheaply. The masked state protects the service, so the precise reason is recorded in server-side telemetry that only the account owner can read.

The practical workflow, then, is a short loop. Capture the full client error text including the principal name and whatever state is shown. Decide which authentication world you are in, SQL or Entra, by looking at the connection method. If the client state is specific, map it directly. If the client state is the generic value, query the server-side telemetry or auditing for the true state. Then, and only then, match the state to a cause from the decoder below and apply the matching fix. The discipline of decoding before retrying is the entire method, and it is what the rest of this article equips you to do for each distinct cause.

## The InsightCrunch 18456 State Decoder

The findable artifact for this article is a decoder that maps the documented error states to their cause and the fix that addresses that cause. State numbers and their meanings are stable and well documented, but Azure SQL masks many of them to the client, so treat the decoder as the mapping to apply once you have the true state from server-side telemetry, and verify any specific state behavior against the current official documentation, because the platform's surfacing of states can change.

| Error state | What it means | Authentication world | First fix to try |
| --- | --- | --- | --- |
| 1 | Generic or masked state; real reason withheld from the client | Either | Retrieve the true state from server-side auditing or telemetry, then re-decode |
| 5 | The login or user does not exist | SQL | Create the login or user, or correct the username spelling and case |
| 6 | A Windows or Entra identity was presented through SQL authentication | Mixed | Connect using the matching authentication method instead |
| 7 | The login exists but is disabled, and a wrong password was also given | SQL | Re-enable the account and verify the password |
| 8 | The password did not match the stored credential | SQL | Correct or rotate the password; check for stale cached credentials |
| 38 | The login is valid but the requested database cannot be opened | Either | Point the connection at the correct database; common for contained users |
| 58 | SQL authentication was attempted against an Entra-only server | Mixed | Switch the client to Entra authentication or enable SQL auth on the server |
| 102 to 122 range | Entra or token-related failures during federated authentication | Entra | Fix token acquisition, the principal provisioning, or the auth mode |

The decoder is the link magnet, but the reasoning behind it is what makes it usable. Two of these states, 5 and 8, are the ones engineers expect, because they correspond to the two textbook mistakes of a missing login and a wrong password. The states that actually consume the most diagnostic time are 38 and 58, because they look like credential problems from the client side while being something else entirely: 38 is a database-routing problem and 58 is an authentication-mode problem, and neither is fixed by touching the password. The remaining work of this article is to take each cause in turn, show how to confirm it is the one you are facing, and give the tested fix.

## Cause One: The Password Is Wrong, Stale, or Cached

The wrong-password case is real and common, and it maps to state 8, sometimes accompanied by state 7 when the account is also disabled. It deserves to be handled first not because it is the most interesting but because eliminating it cleanly stops you from re-entering credentials for the other five causes, which is the single biggest time sink with 18456. The goal here is to confirm the password is genuinely the problem rather than to assume it, because the entire premise of this article is that the assumption is wrong more often than it is right.

### How do I confirm a wrong password is really the cause of 18456?

Test the exact credential in isolation with a minimal client that has no cached state and no integrated-security fallback. If a clean connection with the password typed by hand succeeds, the credential is correct and your application is sending something different. If the clean connection also fails with state 8, the stored password truly does not match and you reset it.

The cleanest confirmation uses a command-line tool that takes the username and password as explicit parameters, so nothing is inherited from a profile or a saved session. With `sqlcmd` you can prove the credential directly:

```bash
sqlcmd -S yourserver.database.windows.net -d yourdatabase -U appuser -P 'the-password-here' -Q "SELECT SUSER_SNAME() AS who, DB_NAME() AS db;"
```

If that returns the principal name and the database, the password is valid and the database context is reachable, which immediately exonerates both the credential and the routing. If it returns 18456, you have reproduced the failure in the simplest possible environment, and now you compare what `sqlcmd` sent against what your application sends. The most frequent divergence is that the application reads the password from a configuration source that is stale: an app setting that was not updated after a rotation, a secret in a vault that a deployment did not refresh, or an environment variable shadowed by a default. The fix is not to change the database; it is to align the source of truth for the credential.

Cached credentials are their own trap. A management tool that connected successfully yesterday may hold a cached entry that no longer matches after a rotation, and it will keep presenting the stale value while you swear you typed the new one. Clearing the saved connection, or starting a fresh tool instance, removes that variable. In application code, a connection pool can hold connections opened under an old credential; those pooled connections do not re-authenticate until they are recycled, so a password rotation can produce a window where new connections fail with 18456 while old pooled ones keep working, which is a confusing partial failure that points straight at pooling rather than at the password itself.

When the password genuinely needs resetting, you do it against the appropriate scope. A server-level login on the logical server is reset in the `master` database, while a contained database user's password is reset inside its own database. Mixing those scopes is itself a cause of confusion, because resetting a password "for the user" in the wrong database changes a different principal than the one failing. For a SQL login at the server level:

```sql
-- Run against the master database on the logical server
ALTER LOGIN appuser WITH PASSWORD = 'a-new-strong-password';
```

For a contained user, the reset runs in the user database and targets the user, not a login, which is the distinction the next cause and the contained-user cause both turn on. The password case closes cleanly once you have confirmed it in isolation, and confirming it in isolation is exactly what prevents you from carrying a false password hypothesis into the harder causes.

## Cause Two: The Login or User Does Not Exist

State 5 means the engine looked for the principal you named and did not find it. This sounds trivial, but on Azure SQL it has a structural subtlety that produces real confusion: the difference between a login, which lives at the logical server level in `master`, and a user, which lives inside a specific database. A principal can exist as one and not the other, and a connection that targets the wrong scope will report that the identity does not exist even though "the account" feels like it obviously does.

### Why does Azure SQL say my login does not exist when I know I created it?

Most often you created a database user but are authenticating at the server level, or you created a server login but the database has no matching user mapped to it. Azure SQL separates server-level logins in master from database-level users, and a principal present in one scope is genuinely absent from the other, which produces state 5.

On a traditional SQL Server you create a login at the server and then map a user in each database to that login, linked by a shared security identifier. Azure SQL Database supports that server-plus-user model for the logical server, but it also strongly encourages contained database users, which exist only inside their database and have no server-level login at all. The two models coexist, and the failure mode appears when an engineer creates a contained user in `appdb` and then tries to authenticate against `master`, or creates a server login in `master` and expects it to work in `appdb` where no user was ever mapped. In both situations the engine truthfully reports that the named principal does not exist in the scope being checked.

Confirming this cause is a matter of asking each scope whether it knows the principal. Connected to `master` with an administrative account, you enumerate server-level logins:

```sql
-- Against master: does a server-level login exist?
SELECT name, type_desc, is_disabled
FROM sys.sql_logins
WHERE name = 'appuser';
```

Connected to the user database, you ask whether a database user exists there:

```sql
-- Against the user database: does a database user exist?
SELECT name, type_desc, authentication_type_desc
FROM sys.database_principals
WHERE name = 'appuser';
```

If the login appears in `master` but no user appears in the database, the principal can authenticate to the server but has nowhere to land, and you create the mapped user. If the user appears in the database but there is no login in `master`, you have a contained user and the connection must target that database directly rather than `master`, which is the contained-user cause covered in depth below. If neither query returns a row, the principal genuinely does not exist anywhere and you create it in the model you intend to use.

Creating a contained database user with its own password, which is the recommended pattern for application identities on Azure SQL, runs inside the target database:

```sql
-- Run inside the application database, not master
CREATE USER appuser WITH PASSWORD = 'a-strong-password';
ALTER ROLE db_datareader ADD MEMBER appuser;
ALTER ROLE db_datawriter ADD MEMBER appuser;
```

Spelling and case are part of this cause more than engineers expect. The principal name comparison can be case sensitive depending on the database collation, and a user created as `AppUser` is not the same string as `appuser` under a case-sensitive collation. A connection that works in one environment and fails in another with state 5, despite an apparently identical username, is frequently a collation-driven case mismatch. Verifying the exact stored name with the queries above, rather than trusting the name you remember typing, resolves that variant quickly.

## Cause Three: The Server Firewall or IP Rule Is Blocking the Client

This cause is the one most often misfiled under 18456, and clearing up the misfiling is itself valuable. A server-level firewall block on Azure SQL does not actually produce 18456. It produces error 40615, with a message that reads close to "Cannot open server 'yourserver' requested by the login. Client with IP address 'x.x.x.x' is not allowed to access the server." Engineers group it with 18456 because the experience is identical from the outside, the connection was refused and you cannot get in, and because the older evergreen phrasing "cannot open server requested by the login" sits right next to "login failed" in everyone's memory. Distinguishing the two is the diagnostic win, because a firewall block and a credential failure have nothing in common except the feeling of being locked out.

### Can the firewall cause something that looks like a login failure?

Yes, and the tell is in the message. A firewall block reports error 40615 and names your client IP address explicitly, saying that address is not allowed to access the server. A true 18456 names a principal and says login failed. If the message contains an IP address and the words "not allowed to access," you are looking at a firewall rule, not a credential.

The reason this lands in the same bucket is the order of the handshake described earlier. The Azure SQL gateway checks the server-level firewall before the engine evaluates the credential, so a firewall block stops the connection at a stage that never reaches authentication. That is precisely why the error number is different: the request was rejected by the gateway's network policy, not by the engine's authentication logic. Reading the actual error number, 40615 for the firewall versus 18456 for the credential, is the fastest possible disambiguation, and it is why capturing the full error text rather than the paraphrase "it said login failed" matters during an incident.

Confirming a firewall cause means inspecting the rules and the client's apparent IP. The address the service sees is the public egress address of wherever your client sits, which for a developer behind a corporate network, a VPN, or a cloud NAT is often not the address shown by a local network configuration. You list the server-level firewall rules and check whether the client's real public address falls inside any allowed range:

```bash
# List the logical server's firewall rules
az sql server firewall-rule list \
  --resource-group myresourcegroup \
  --server yourserver \
  --output table
```

To learn the public address the service actually sees, query it from the same network path the client uses, then compare it against the rules. If the address is outside every rule, you add a rule scoped as narrowly as the situation allows:

```bash
# Add a narrowly scoped firewall rule for a known client address
az sql server firewall-rule create \
  --resource-group myresourcegroup \
  --server yourserver \
  --name allow-office-egress \
  --start-ip-address 203.0.113.10 \
  --end-ip-address 203.0.113.10
```

There is a second layer worth knowing. Azure SQL has both server-level firewall rules and database-level firewall rules, and the gateway evaluates them together; a database-level rule can admit a client that the server-level rules do not, and the interaction occasionally surprises people who set one and forget the other. There is also the "Allow Azure services" toggle, which permits connections from Azure-internal address ranges and is convenient but broad, and an exception that allows access through private endpoints or service endpoints inside a virtual network, which bypasses the public IP firewall entirely. When a client that should be allowed is still blocked, the question is which of these paths it is actually traversing, because a client routed through a private endpoint is not subject to the public firewall at all and a public client is not helped by a private endpoint. Matching the client's real network path to the rule that governs that path is the core of the fix, and it is why the firewall cause rewards a few minutes of confirming the IP and the path rather than reflexively widening a rule.

## Cause Four: A Contained Database User Is Connecting to the Wrong Database

This is the cause that produces the most "but the credential is correct" frustration, and it is the one the namable claim of this article is built to catch. A contained database user exists only inside its own database and has no presence in `master`. When a connection authenticates such a user but the connection's database context is `master`, or is left unset so the gateway routes it to the server default, the engine cannot find that user in the database it is being asked to open, and the login fails. The password is right, the user genuinely exists, and the connection still fails, which is exactly the situation that drives engineers to retype a credential that was never the problem. This maps to state 38, the "valid login but cannot open the requested database" path, sometimes surfacing as a generic state to the client.

### Why does my contained database user get error 18456 with the right password?

Because the connection is reaching master, where the contained user does not exist, instead of the user's own database. A contained user has no server-level login, so it can only authenticate inside its database. Set the connection's database, the Initial Catalog, to that specific database and the authentication succeeds.

The structural reason is the containment model itself. Containment was designed so a database carries its own users and can be moved between servers without re-creating server-level logins, which is excellent for portability and for least-privilege isolation. The trade-off is that the connection must declare which database it intends to open, because there is no server-level identity to fall back on. A traditional server login can connect to `master` and then switch databases, because the server knows the login. A contained user cannot, because the server does not know it; only the user database does. So the connection string must name the database, and if it does not, the contained user is effectively invisible at the point where authentication happens.

Confirming this cause is quick once you suspect it. Check whether the failing principal is a contained user, meaning it appears in the database's principals with a password-based authentication type and has no matching server login:

```sql
-- Inside the application database
SELECT name, type_desc, authentication_type_desc
FROM sys.database_principals
WHERE name = 'appuser';
-- authentication_type_desc of DATABASE indicates a contained user
```

Then inspect the connection string the failing client uses and confirm whether it sets the database. In an ADO.NET style connection string the relevant key is `Initial Catalog` or its alias `Database`, and its absence or a value of `master` is the smoking gun:

```text
Server=tcp:yourserver.database.windows.net,1433;
Initial Catalog=appdb;
User ID=appuser;
Password=the-password;
Encrypt=True;
```

The fix is to set `Initial Catalog` to the contained user's database, here `appdb`, so the gateway routes the authentication to the database that actually holds the user. With `sqlcmd` the equivalent is the `-d` parameter naming the database, and omitting it is the command-line version of the same mistake:

```bash
# Correct: name the database so the contained user is found
sqlcmd -S yourserver.database.windows.net -d appdb -U appuser -P 'the-password' -Q "SELECT DB_NAME();"

# Wrong: no database named, routes to master where the contained user does not exist
sqlcmd -S yourserver.database.windows.net -U appuser -P 'the-password' -Q "SELECT 1;"
```

There is a related variant where the database name is correct but the database itself is unavailable: paused in the serverless tier, mid-failover, or recently restored under a different name. In those cases the connection cannot open the database for a reason other than containment, and the failure can again surface as a database-open error rather than a clean credential failure. Distinguishing "the database does not hold this user" from "the database cannot be opened right now" is a matter of testing the same database with an administrative account; if the admin can open it and the contained user cannot, the problem is the user's presence and scope, and if no one can open it, the problem is the database's availability, which crosses over into the sibling error covered later. The contained-user cause is the clearest example of the article's thesis: the credential is innocent, the routing is guilty, and only reading the situation rather than the password reveals it.

## Cause Five: A Microsoft Entra Authentication or Token Problem

When the connection authenticates with Microsoft Entra ID rather than a SQL password, error 18456 takes on an entirely different set of root causes, because the credential is no longer a password the database stores. It is a token issued by the Entra identity platform, presented to the database, and validated against a principal that an administrator has provisioned inside the database. Any link in that chain can break: the token may never have been acquired, it may be acquired for the wrong audience or scope, the principal may not exist in the database, or the server may be configured to reject the kind of identity the token represents. The failure still reads as login failed, but the fix lives in the identity platform and the database's Entra configuration rather than in any password.

### Can a Microsoft Entra problem cause error 18456?

Yes. With Entra authentication the database validates a token rather than a password, so 18456 can mean the token was never acquired, was issued for the wrong resource, or names a principal that was never created in the database. The fix is to correct token acquisition or to provision the Entra principal as a database user, not to change a password.

The first branch is whether a token was acquired at all. An application using a managed identity, a service principal, or an interactive user sign-in must obtain a token for the SQL resource before it can authenticate, and a token acquisition that silently fails or returns a token for the wrong resource produces a connection that has nothing valid to present. The resource the token must target is the Azure SQL Database resource identifier, and a token minted for Microsoft Graph or for a different audience will be rejected even though it is a perfectly valid token for its actual audience. When an application connects with a managed identity, the identity must be enabled on the host, assigned where the code expects it, and granted access in the database; a system-assigned identity that the code assumes is user-assigned, or the reverse, is a frequent source of a token that resolves to an unexpected principal or no principal.

The second branch is whether the Entra principal exists in the database. Just as a SQL contained user must be created inside its database, an Entra identity must be provisioned as a database user mapped to that identity. Creating an Entra user references the identity by its name and declares it as an external principal:

```sql
-- Run in the target database, connected as an Entra admin
CREATE USER [appservice-identity] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [appservice-identity];
ALTER ROLE db_datawriter ADD MEMBER [appservice-identity];
```

The name in brackets must match the display name or the identity the token will carry, and a mismatch here means the token authenticates a principal the database has never heard of, which fails. For a managed identity, the bracketed name is typically the name of the managed identity resource; for a user, it is the user principal name; for an application registration used as a service principal, it is the application's display name, and getting the right one of those three is part of the fix. Provisioning an Entra user also requires that the database have an Entra administrator configured at the logical-server level, because only an Entra-authenticated administrator can create external-provider users, and a server with no Entra admin set cannot have Entra users created at all.

The third branch is the server's authentication-mode configuration, which crosses into the next cause but deserves naming here. A logical server can be set to allow both SQL and Entra authentication, or to allow Entra authentication only. On an Entra-only server, a SQL password login is rejected by policy, and on a server without an Entra admin, an Entra token has no administrator path to validate against. Reading the server's Entra settings tells you whether the token even has a chance:

```bash
# Inspect the Entra (Azure AD) administrator configured on the server
az sql server ad-admin list \
  --resource-group myresourcegroup \
  --server yourserver \
  --output table

# Inspect whether the server enforces Entra-only authentication
az sql server ad-only-auth get \
  --resource-group myresourcegroup \
  --server yourserver
```

Confirming the Entra cause therefore proceeds in layers: verify a token is acquired for the correct SQL resource, verify the principal the token represents has a matching database user, and verify the server's authentication mode admits that identity type. Token acquisition can be tested independently of the database by requesting a token for the SQL resource from the same identity context the application uses and inspecting that it returns successfully and carries the expected principal. Once the token is known good, the remaining failure is almost always a missing or misnamed database user or a server mode that excludes the identity, both of which are configuration fixes rather than credential resets. Managed-identity based access is covered end to end in the dedicated guide on configuring managed identities correctly, which walks through the assignment, the grant, and the verification in one place, and pairing that with this decoder turns an opaque Entra 18456 into a short checklist.

## Cause Six: The Account Is Disabled, Expired, or Mode-Mismatched

The final cause gathers the states that mean the principal and credential are recognized but the engine refuses the login on policy grounds. A disabled login produces state 7 when a wrong password accompanies it, and a recognized-but-refused login can surface in the higher states. The simplest version is an account that was deliberately disabled, perhaps during an offboarding or a security response, and then expected to keep working. The engine knows the login, accepts that the password could be checked, and still refuses because the account is administratively turned off.

Checking and re-enabling is direct. The `is_disabled` column on the server logins view or the equivalent state on a database user tells you immediately whether the account is off:

```sql
-- Against master for a server login
SELECT name, is_disabled FROM sys.sql_logins WHERE name = 'appuser';

-- Re-enable if it was disabled intentionally and should be on
ALTER LOGIN appuser ENABLE;
```

The mode-mismatch version is state 58 and state 6, and it is worth treating carefully because it is genuinely confusing. State 58 appears when a client attempts SQL authentication against a server that has been set to Entra-only authentication; the server rejects the SQL credential not because it is wrong but because SQL passwords are not accepted at all. State 6 is the mirror situation where an identity that belongs to one authentication world is presented through the mechanism of the other, such as an Entra account name pushed through a SQL-password code path. The fix for both is not to fix the credential but to align the authentication method the client uses with the method the server accepts. If the server is Entra-only by deliberate policy, the client must switch to Entra authentication. If SQL authentication is genuinely required, an administrator must change the server to allow it, which is a policy decision rather than a quick toggle, because Entra-only mode is often set intentionally to enforce centralized identity.

### How do I tell a disabled account from a wrong password?

Query the account's disabled flag directly. A disabled SQL login shows `is_disabled = 1` in `sys.sql_logins`, and the engine refuses it regardless of the password. If the flag is zero and the login still fails, the password or another cause is responsible, so the flag cleanly separates a policy refusal from a credential refusal.

Account expiry and password-policy enforcement add a wrinkle on logins that carry expiration or must-change settings. A login whose password is flagged to expire, or one created with a check-policy setting that demands a change at next login, can refuse a connection that does not satisfy the policy even when the password string is correct. These are less common on Azure SQL contained users, which typically do not carry the same Windows-style password policy machinery, but they appear on server-level logins migrated from environments where those policies were set. Inspecting the login's policy flags and clearing or satisfying them resolves the case. The unifying idea across this sixth cause is that the credential is correct and the principal is known, yet a policy, a disabled flag, or an authentication-mode setting stands between the client and the database, and the fix changes that policy or that mode rather than the password.

## Putting the Diagnosis Together: A Repeatable Flow

With the six causes mapped, the diagnosis becomes a short, repeatable sequence rather than a guessing game, and running it the same way every time is what compresses the fix to minutes. The flow starts at the network and works inward, because failures earlier in the handshake masquerade as failures later, and skipping ahead to the credential is exactly the mistake the article exists to prevent.

Begin by reading the exact error text, the full number and the principal name, not a paraphrase. If the number is 40615 and the message names an IP address, you are at the firewall and you go straight to the firewall rules; this is not an 18456 and no credential work will help. If the number is 18456, capture whatever state the client shows and note the principal name, then decide the authentication world by how the connection authenticates: a password in the connection string is SQL authentication, a token or an Entra method is Entra authentication. That single branch routes you toward the SQL causes of wrong password, missing login, contained-user routing, and disabled account, or toward the Entra causes of token acquisition, principal provisioning, and authentication mode.

If the client state is specific, map it through the decoder. State 5 sends you to confirm the principal exists in the scope you are connecting to. State 8 sends you to confirm the password in isolation with a clean client. State 38 sends you to check whether the connection names the right database for a contained user. State 58 sends you to compare the client's authentication method against the server's accepted modes. If the client state is the masked generic value, retrieve the true state from server-side auditing or telemetry before mapping, because guessing from the masked state is how engineers end up resetting passwords that were never wrong. Each mapped state has its confirming command from the sections above, and the confirmation is what converts a hypothesis into a fact before you change anything.

The reason to confirm rather than fix-and-see is that several of these causes share symptoms and a blind fix can mask the real one. Widening a firewall rule appears to fix a contained-user routing problem if the engineer also happened to correct the database in the same change, leaving a too-broad firewall rule and a wrong belief about the cause. Resetting a password appears to fix a disabled account if someone re-enabled the account in parallel. The discipline of confirming the specific cause, applying the single matching fix, and then verifying with the confirming command keeps the diagnosis honest and the security posture tight, which matters because every one of these fixes touches access to a database.

## Preventing 18456 Before It Happens

Prevention for 18456 is mostly a matter of removing the conditions that let the six causes arise, and a few deliberate choices at setup time eliminate most of the recurring incidents. The strongest single move is to enable Azure SQL Auditing to a durable sink before you need it, because the masked client state is the largest obstacle to fast diagnosis and auditing is what gives you the true state on demand. An audit configured to a Log Analytics workspace lets you query authentication failures with the precise reason, turning a future incident from a guessing exercise into a lookup.

Credential management prevents the password and missing-login causes. Storing application credentials in a managed secret store and rotating them through a process that updates every consumer at once removes the stale-credential window, and recycling connection pools as part of a rotation closes the pooled-connection gap where new connections fail while old ones still work. Better still, moving application identities from SQL passwords to managed identities removes the password as an artifact entirely, which eliminates the wrong-password and stale-credential causes by construction; there is no password to rotate, leak, or cache, and access is granted to the identity directly. The managed-identity path requires the provisioning described above, but once set up it is markedly more robust against the most common 18456 triggers, and the broader identity model behind it is the subject of the dedicated security guide for Azure SQL.

The contained-user routing cause is prevented by convention: always set the database in every connection string and every tool profile, never rely on a server default, and standardize on contained users with the database named explicitly so the routing is never ambiguous. Code review can catch a connection string missing its `Initial Catalog` before it reaches production, and a connection-string template that includes the database as a required field makes the omission hard to commit. The firewall cause is prevented by managing rules as infrastructure-as-code so the allowed ranges are reviewed and version-controlled rather than added ad hoc during incidents, and by preferring private endpoints for production traffic so the public firewall is not the access path at all for the workloads that matter most. The Entra causes are prevented by setting the server's Entra administrator deliberately, choosing the authentication mode on purpose rather than discovering it during a failure, and provisioning each identity's database user as part of the same deployment that creates the identity, so a new service never reaches production without its database principal already in place.

Documenting the chosen model is itself prevention. A team that has written down whether it uses contained users or server logins, SQL or Entra authentication, public firewall or private endpoint, and that names the database in every connection by standard, will not generate the ambiguity that produces most 18456 incidents. The error thrives on uncertainty about which model is in use, and removing that uncertainty at the design stage is cheaper than decoding states under incident pressure.

## Related Failures Often Confused With 18456

Several Azure SQL errors live close enough to 18456 that engineers conflate them, and separating them is part of becoming fast at the real diagnosis. The closest sibling is error 40613, "Database is not currently available," which appears when the database is mid-failover, paused in the serverless tier, or otherwise temporarily unreachable. It is transient and the correct response is a retry with backoff, not a credential change, which is the opposite of the instinct 18456 provokes; the detailed treatment of that transient error and its retry pattern is covered in the dedicated guide on fixing the 40613 unavailable error, and recognizing 40613 as a database-availability problem rather than an access problem is the disambiguation that matters. Because a contained user against an unavailable database can produce a database-open failure, the two can shade into each other, and the test is whether an administrative account can open the database: if yes, the contained user's routing or provisioning is the issue, and if no, the database's availability is.

Error 40615 is the firewall block discussed under cause three, and its tell is the explicit client IP address in the message. Error 40532, "Cannot open server requested by the login," appears in older connection scenarios and in cases where the server name in the connection is malformed or the routing to the logical server fails, and it again reads like a login problem while being a connection-target problem. Error 4060, "Cannot open database requested by the login," is the on-premises-flavored cousin of the contained-user routing failure and names the database explicitly, which is a useful confirmation that the database context, not the credential, is the issue. The throttling error 40501, "The service is currently busy," is unrelated to authentication entirely but gets swept into the same "it would not connect" bucket during a noisy incident, and keeping it separate prevents wasted credential work when the real problem is resource pressure.

The unifying lesson across these neighbors is the same one the whole article turns on: the exact error number and the exact message text are the signal, and reading them precisely routes you to the right family of cause before you spend any effort. An engineer who reflexively reads "login failed" and reaches for the password will mishandle 40613, 40615, 40532, 4060, and 40501 alike, because every one of them can feel like a login failure from the outside. An engineer who reads the number and the words handles each correctly on the first attempt.

## Recurring Real-World Scenarios and Their States

The six causes describe the machinery, but engineers hit them in recognizable patterns at work, and learning the patterns lets you skip straight to the likely cause when the shape of the situation is familiar. Each pattern below is a recurring case engineers report, framed as a problem shape with the state it tends to carry and the move that resolves it.

The first pattern is the freshly deployed application that has never connected once. Here the most likely culprits are a principal that was never provisioned in the right scope, state 5, or a connection string that omits the database for a contained user, state 38. A service that has worked elsewhere and fails only in a new environment points at environment-specific configuration: a different server, a different secret value, or a deployment that created the identity but skipped the database user. The move is to verify the principal exists in the scope being connected to and that the connection names the database, because a first-time deployment failure is far more often a provisioning or routing gap than a wrong password.

The second pattern is the application that worked yesterday and fails today after no obvious change. This shape points at something that changed outside the application's own code: a rotated secret that did not propagate, an account disabled during a review, a server switched to Entra-only authentication by a security initiative, or a firewall rule removed during a cleanup. The state varies with the trigger, which is exactly why retrieving the true state is the right first move rather than guessing. A sudden failure across all instances at once suggests a server-side or credential-store change, while a failure that grows as instances recycle suggests a rotation propagating unevenly through a connection pool.

The third pattern is the intermittent failure where some connections succeed and others fail. This is the connection-pool signature almost every time: pooled connections opened under an old credential keep working while new connections fail after a rotation, producing a failure rate that tracks pool recycling rather than any clean on-or-off behavior. The move is to recycle the pool and confirm every credential consumer has the current value, and the longer-term answer is token-based access that removes the rotation entirely.

The fourth pattern is the contained user that authenticates against master. An engineer creates a user inside the application database, tests it with a tool that happens to default to that database, and it works; then the application connects without naming the database, lands on master, and fails. The state is 38 or a masked generic value, the password is provably correct in the tool, and the difference is entirely the database context. The move is to add the database to the application's connection string, and the prevention is a connection-string template that requires the database as a field.

The fifth pattern is the Entra-only server rejecting a SQL login. A platform team enforces Entra-only authentication to centralize identity, and an older application still configured for a SQL password suddenly cannot connect. The state is 58, the credential is irrelevant, and the move is to migrate the application to Entra authentication or, if SQL authentication is genuinely required for that workload, to have an administrator reconsider the server's mode as a deliberate decision rather than reverting it reflexively.

The sixth pattern is the report or analytics connection that fails while the transactional application succeeds against the same server. This frequently turns out to be a separate principal with a different scope or a different database mapping: the reporting identity exists in master but has no user in the analytics database, or targets a read replica with a different access configuration. The move is to confirm the reporting principal's scope and database mapping independently of the application's, because two connections to the same server can fail for entirely different reasons depending on which principal and which database each one uses.

Reading the pattern first and confirming the state second is faster than running the full flow from scratch every time, and the patterns above cover the large majority of what engineers actually encounter. The discipline remains the same: the pattern suggests the cause, the state and the confirming command prove it, and only then do you apply the fix.

## Tool-Specific Behavior: SSMS, Azure Data Studio, sqlcmd, and Drivers

The 18456 you see depends partly on the tool that produced it, because each client surfaces the error and the state differently and each has its own ways of hiding or revealing the identity actually presented. Knowing how your specific tool behaves shortens the gap between the message and the cause.

SQL Server Management Studio shows the error number and a state in its connection-failure dialog, but the state it shows for Azure SQL is frequently the masked generic value, so the dialog confirms you have an 18456 without always revealing why. SSMS also remembers connections, and a saved connection can carry a database context and a cached credential that differ from what you think you are sending, which is a common source of the works-in-the-tool-fails-in-the-app divergence. When diagnosing with SSMS, open a fresh connection dialog rather than reusing a saved entry, set the database explicitly under the connection options rather than leaving the default, and read the principal name in the error against the one you intended.

Azure Data Studio behaves similarly and adds first-class Entra authentication options in its connection panel, which makes it a useful tool for isolating whether an Entra failure is a token problem or a provisioning problem. Connecting with an interactive Entra sign-in that you know is a valid administrator, and seeing whether that succeeds where the application's identity fails, separates a broken token-acquisition path in the application from a missing database user, because the interactive sign-in proves the server accepts Entra identities while the application's identity does not yet have a database principal.

The command-line client sqlcmd is the cleanest diagnostic instrument precisely because it carries no saved state when you pass everything explicitly. A sqlcmd invocation with the server, database, username, and password all on the command line reproduces a connection with no cached credential, no integrated-security fallback, and no default database surprise, which is exactly what you want when isolating a cause. Its database parameter makes the contained-user routing issue easy to demonstrate: include it and a contained user connects, omit it and the same user fails, with nothing else changed. For Entra authentication, sqlcmd supports authentication-method switches that let you reproduce a token-based connection from the same identity context the application uses, turning an abstract Entra failure into a concrete, repeatable test.

Application drivers add their own layer because they translate a connection string into the handshake, and the translation is where subtle problems hide. A driver may default to a behavior the engineer did not intend: falling back to integrated security when a username is absent, applying a default database, caching connections in a pool, or interpreting an ambiguous connection-string key differently from another driver. The same logical credentials can succeed through one driver and fail through another because of these defaults. When an application fails where a tool succeeds, dumping the effective connection string the driver actually used, with secrets redacted, and comparing it field by field against the working tool connection reveals the divergence. The principal name in the 18456 message is again the anchor: it tells you which identity the driver actually presented, and if that name is not the one you expected, the driver's handling of the connection string is the place to look rather than the database.

A final tooling note concerns timeouts and retries layered on top of authentication. Some drivers and frameworks wrap connections in retry logic that re-attempts on failure, and a retry loop around an 18456 will hammer the server with identical failing attempts, because 18456 is not transient and the retry cannot help. Worse, repeated failed logins can trigger protective throttling, turning a clean configuration problem into a noisier incident with added latency. Configuring retry logic to distinguish the transient errors that warrant a retry from the deterministic ones like 18456 that do not, keeps a simple credential or routing problem from escalating into a storm of failed attempts that obscures the original cause.

## A Worked Reproduction: Triggering and Confirming Each State

Diagnosis sticks when you have triggered each cause yourself and watched the state change, so the most durable way to internalize the decoder is to reproduce the states deliberately in a throwaway logical server. The walkthrough below builds each cause on purpose, which is the inverse of fixing it, and the inversion is instructive: seeing exactly what produces state 5 versus state 38 makes both unmistakable the next time they appear under incident pressure.

Start by provisioning a logical server and a database you can discard afterward, then create two principals to work with, a server-level login mapped into the database and a contained user that lives only in the database. The contrast between the two is the engine of half the causes.

```sql
-- In master: a server-level login
CREATE LOGIN serverlogin WITH PASSWORD = 'Strong-Pass-1';

-- In the application database: a user mapped to that login
CREATE USER serverlogin FROM LOGIN serverlogin;
ALTER ROLE db_datareader ADD MEMBER serverlogin;

-- In the application database: a contained user with no server login
CREATE USER containeduser WITH PASSWORD = 'Strong-Pass-2';
ALTER ROLE db_datareader ADD MEMBER containeduser;
```

To reproduce the wrong-password cause, connect as either principal with a deliberately incorrect password and observe the refusal that corresponds to state 8 in server-side telemetry. The point of doing this on purpose is to fix in your memory that a wrong password produces a clean, repeatable refusal that does not change with the database context, which distinguishes it from the routing causes that do change with context.

```bash
# Wrong password: refusal maps to the password-mismatch state
sqlcmd -S yourserver.database.windows.net -d appdb -U containeduser -P 'Wrong-Pass' -Q "SELECT 1;"
```

To reproduce the missing-principal cause, connect as a name that was never created, or connect the contained user against master where it does not exist. The first produces the does-not-exist refusal, state 5, and the second produces the cannot-open-database refusal that the contained user triggers when it reaches the wrong scope.

```bash
# Never-created name: does-not-exist refusal
sqlcmd -S yourserver.database.windows.net -d appdb -U ghostuser -P 'anything' -Q "SELECT 1;"

# Contained user against master: routing refusal
sqlcmd -S yourserver.database.windows.net -d master -U containeduser -P 'Strong-Pass-2' -Q "SELECT 1;"
```

The second command is the single most valuable reproduction in the set, because it fails with a correct password and a real user, which is the exact experience that drives the reflexive and useless password retry. Run it once with the database set to master and watch it fail, then run it again with the database set to the application database and watch it succeed, changing nothing but the database context. That single before-and-after, the same credential failing and then succeeding purely on database context, is the demonstration that proves the contained-user routing cause more convincingly than any explanation.

```bash
# Same contained user, correct password, only the database differs: now it works
sqlcmd -S yourserver.database.windows.net -d appdb -U containeduser -P 'Strong-Pass-2' -Q "SELECT DB_NAME();"
```

To reproduce the disabled-account cause, disable the server login and connect as it, observing that even a correct password is refused while the account is off. Re-enabling it restores access, which confirms that the disabled flag, not the credential, governed the refusal.

```sql
-- In master: disable, then a login attempt with the correct password still fails
ALTER LOGIN serverlogin DISABLE;
-- ...attempt connection as serverlogin with Strong-Pass-1, observe refusal...
ALTER LOGIN serverlogin ENABLE;
```

To reproduce the authentication-mode mismatch, set the server to Entra-only authentication and then attempt a SQL password connection, which is refused by policy with the mode-mismatch state regardless of the credential. Reverting the server to allow SQL authentication restores the SQL path, demonstrating that the server's mode, not the password, controlled the outcome. Running these reproductions in a disposable environment, ideally in a structured lab where each one is scripted, builds the recognition that turns a future incident into a fast, confident decode rather than a slow, anxious guess.

## Reading Login Failures in Auditing With KQL

When Azure SQL Auditing is enabled to a Log Analytics workspace, the failed logins become queryable records, and a short KQL query turns the masked client experience into a precise, historical view of why logins are failing and how often. This is the payoff of enabling auditing before an incident: instead of reconstructing a failure from a vague client message, you query the record of exactly what the engine decided and when.

The audit data captures authentication events with fields for the principal, the action, the success or failure result, and timing, which lets you filter to failures and group them to see the shape of the problem. A query that isolates failed authentication events over a recent window, and counts them by principal and by client, reveals whether failures concentrate on one identity, one source, or are spread broadly, and that distribution is itself diagnostic.

```kusto
// Failed login events in the last day, grouped by principal and client
AzureDiagnostics
| where Category == "SQLSecurityAuditEvents"
| where action_name_s == "DATABASE AUTHENTICATION FAILED"
    or action_name_s == "LOGIN FAILED"
| where TimeGenerated > ago(1d)
| summarize Failures = count() by server_principal_name_s, client_ip_s, bin(TimeGenerated, 1h)
| order by Failures desc
```

The exact field and category names depend on your auditing configuration and the schema in effect, so confirm them against your own workspace and the current schema rather than assuming the names above are universal, because the auditing schema evolves and the exact columns can differ by setup. The shape of the analysis, though, is durable: filter to authentication failures, group by the principal and the source, and read the distribution.

A concentration of failures on one principal from one client right after a deployment points at a provisioning or connection-string problem for that specific service, which sends you to verify that identity's database user and its connection's database context. A broad scatter of failures across many principals starting at a single moment points at a server-side change, an authentication-mode switch or a firewall edit, that affected everyone at once. A failure rate that climbs gradually as time passes after a credential change points at the connection-pool window, where new connections fail while old pooled ones age out. Reading the temporal and per-principal shape of the failures in auditing often identifies the cause before you have looked at a single connection string, because the pattern in the aggregate carries information that no single error message does.

Auditing also closes the loop on the masked-state problem that makes Azure SQL 18456 harder than its on-premises equivalent. The client is denied the precise reason on purpose, but the workspace records the engine's actual decision, so the query above, refined to surface the recorded reason where the schema exposes it, recovers the localizing detail that the client withheld. Building a saved query or a workbook around failed authentications, and keeping it ready before you need it, converts the next 18456 incident from an investigation into a lookup, which is the highest-leverage preparation an engineer can make against this error.

## Fixing 18456 Without Weakening Security

Every remediation for this error touches access to a database, which means a careless fix can resolve the symptom while quietly opening a hole. The discipline that makes the diagnosis fast also keeps the fix tight, because confirming the specific cause means you change exactly one thing rather than reaching for the broadest change that might work. The broad changes are tempting under pressure and each one carries a cost worth naming.

Widening a firewall rule is the most common over-correction. When a client cannot connect, opening a large address range or enabling all Azure-internal traffic appears to fix the problem and often does, but it admits far more than the one client that needed access, and the rule tends to outlive the incident because nobody remembers to tighten it later. The disciplined fix is to confirm the client's real egress address and add a rule for that address or a narrow range, and for production traffic to prefer a private endpoint so the public surface is not the access path at all. A rule scoped to one address is both the correct fix and the more secure one, and the narrow scope is no slower to apply than the broad one once you have confirmed the address.

Over-granting roles is the analogous mistake on the principal side. When a newly provisioned user fails and the engineer is unsure which permissions it needs, the shortcut is to grant a broad administrative role and move on, which makes the failure disappear and leaves the principal with far more authority than its workload requires. The disciplined alternative is to grant the specific database roles the workload actually uses, the reader and writer roles for an application that reads and writes, and to add narrower permissions only as a real need appears. The 18456 you are fixing is an authentication failure, the principal could not log in at all, so resolving it does not require elevated authorization; it requires the principal to exist and to be admitted, and the authorization it then carries should be the least that its job demands.

Reverting an authentication-mode decision deserves the same care. When an Entra-only server rejects a SQL login with state 58, the fastest path to a working connection is to switch the server back to allowing SQL authentication, and that switch will indeed make the login succeed. But the Entra-only mode was very likely set on purpose to centralize identity and eliminate standalone passwords, and reverting it to fix one application unwinds a deliberate security posture for the whole server. The disciplined move is to migrate the failing application to Entra authentication so it fits the intended model, and to treat any change to the server's mode as a decision made with the team that set it rather than a unilateral fix during an incident. Token-based access is also the more durable answer, because it removes the password that would otherwise need to be created, stored, rotated, and protected.

Avoiding credential sprawl is the prevention-side version of the same principle. Each new SQL login and password is another secret to store, rotate, audit, and eventually leak, and the easiest 18456 to fix is the one that never happens because there is no password at all. Consolidating application access onto managed identities, granting each identity exactly the database roles it needs, and provisioning that database user as part of the same deployment that creates the identity, removes whole categories of this error while keeping access auditable and least-privilege by default. The security guide for Azure SQL develops this model in full, and the through-line is consistent: the fix that addresses the confirmed cause precisely is almost always the fix that also keeps the database's access posture intact, while the broad fix that papers over an unconfirmed cause is the one that tends to leave exposure behind.

## The Verdict on Error 18456

The defensible position on 18456 is that the error number is the least informative part of the message and the state is the most informative, so the entire diagnostic value lives in reading the state and, on Azure SQL, in retrieving the true state from server-side telemetry when the client masks it. The six causes, a wrong or stale password, a missing login or user, a firewall block that is really 40615, a contained user reaching the wrong database, an Entra token or provisioning problem, and a disabled account or mode mismatch, are structurally distinct, and each has a confirming command and a single matching fix. The most expensive mistake is the reflexive password retry, because it cannot fix four of the six causes and it costs time on the two it might.

The namable rule to carry away is the state-number rule: the login-failed state narrows the cause before any retry, so reading it, bad password versus missing login versus database context versus authentication mode, is the first diagnostic step and the retry is the last. Internalize the handshake order so you know that firewall failures never reach authentication and that a contained user must name its database, and you will route almost every 18456 to its real cause in the first minute. The error rewards reading over guessing more than almost any other Azure SQL failure, and the engineer who decodes it is the one who stops losing afternoons to a credential that was correct all along.

To put the decoder into practice on a live database, you can reproduce each of these six states in a controlled lab and drill the matching fix until the routing is automatic, which is exactly what the companion platforms are built for: [run the hands-on Azure labs and command library on VaultBook](https://vaultbook.net/tools/azure-labs.html) to stand up a logical server, create contained and server-level principals, and reproduce each state on demand, and [work through scenario-based troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) to practice reading a state and choosing the fix under time pressure. The deeper authentication model behind these causes is covered in the [Azure SQL security guide on authentication and encryption](/2024/02/26/azure-sql-security-guide/), the server-and-database principal model that explains the login-versus-user distinction is detailed in the walkthrough of [Azure SQL Database internals](/2022/02/07/azure-sql-database-internals/), the transient sibling error is handled in the guide to [fixing the Azure SQL 40613 unavailable error](/2022/08/15/fix-azure-sql-40613-unavailable/), and the token-based path that removes passwords entirely is laid out in [setting up managed identities the right way](/2023/04/17/configure-managed-identities/).

## Frequently Asked Questions

### Q: What does Azure SQL error 18456 login failed mean?

Error 18456 is the database engine's generic code for a refused login, raised during the authentication handshake after a client presents an identity but before any query runs. On its own it only tells you the engine declined to authenticate the principal. The useful detail lives in the companion error state, a small integer that classifies why the engine refused: a wrong password, a principal that does not exist, a database the principal cannot open, or an authentication-mode mismatch. On Azure SQL Database the service often masks the precise state to the connecting client to prevent username enumeration, recording the true state in server-side telemetry instead. So 18456 by itself means only "login refused," and the real diagnosis comes from reading the state, which is why the first step is always to decode the state rather than to retype the credential.

### Q: How do I read the 18456 error state to find the cause?

Capture the full client error including the state and the principal name, then decide whether the connection uses SQL or Entra authentication. If the client shows a specific state, map it directly: state 5 means the login or user does not exist, state 8 means the password did not match, state 38 means the principal is valid but the requested database cannot be opened, and state 58 means SQL authentication was attempted against an Entra-only server. If the client shows the generic masked state, retrieve the true state from Azure SQL Auditing or the logical server's diagnostic telemetry before mapping, because the masked value hides the reason on purpose. Once you have the true state, each one points to a confirming command and a single matching fix, which turns an opaque refusal into a localized, actionable cause.

### Q: Does a wrong password cause an 18456?

Yes, a wrong password is a genuine cause and maps to state 8, but it is the cause engineers overestimate. The premise of fast diagnosis is to confirm the password is really the problem rather than assume it. Test the exact credential in a clean command-line client such as sqlcmd with the username and password passed explicitly, so nothing is inherited from a cached session or an integrated-security fallback. If the clean client succeeds, the password is correct and your application is sending something different, usually a stale value from a configuration source that was not updated after a rotation, or a pooled connection still using the old credential. If the clean client also fails with state 8, the stored password truly does not match and you reset it against the correct scope, master for a server login or the user database for a contained user.

### Q: Can the server firewall cause an 18456 login failure?

A firewall block does not actually produce 18456; it produces error 40615 with a message naming your client IP address and saying that address is not allowed to access the server. Engineers conflate the two because both feel like being locked out, but the Azure SQL gateway checks the firewall before the engine evaluates any credential, so a firewall rejection stops the connection before authentication even begins. The tell is the message: a firewall block contains an IP address and the phrase about not being allowed to access the server, while a true 18456 names a principal and says login failed. Confirm by listing the server firewall rules and comparing them against the client's real public egress address, which is often different from a local network address because of VPNs, NAT, or corporate egress. Add a narrowly scoped rule for the confirmed address rather than widening access broadly.

### Q: Why does a contained database user get error 18456?

A contained database user exists only inside its own database and has no server-level login in master, so it can only authenticate inside that database. When the connection's database context is master, or is left unset and routed to the server default, the engine cannot find the contained user in the database it is being asked to open, and the login fails even though the password is correct and the user genuinely exists. This maps to state 38, the valid-login-but-cannot-open-database path. The fix is to set the connection's database explicitly: the Initial Catalog or Database key in an ADO.NET connection string, or the -d parameter in sqlcmd, must name the contained user's database. Confirm the user is contained by checking that its authentication_type_desc is DATABASE in sys.database_principals and that no matching server login exists, then point the connection at the right database.

### Q: Can an Entra authentication problem cause 18456?

Yes, and with Entra authentication the cause is never a stored password because the credential is a token issued by the identity platform. An Entra 18456 usually means one of three things: the token was never acquired or was acquired for the wrong resource, the principal the token represents was never created as a database user, or the server's authentication mode rejects that identity type. Verify a token is obtained for the Azure SQL resource specifically, not for Microsoft Graph or another audience. Verify the Entra identity has a matching database user created with CREATE USER FROM EXTERNAL PROVIDER, with the bracketed name matching the managed identity, user principal name, or application display name the token carries. Verify the server has an Entra administrator set and check whether it enforces Entra-only authentication. The fix lives in token acquisition or principal provisioning, never in a password reset.

### Q: What is the difference between error 18456 and error 40613?

Error 18456 is an access failure: the engine refused to authenticate the principal for a reason captured in the state. Error 40613, "Database is not currently available," is an availability failure: the database is temporarily unreachable because it is mid-failover, paused in the serverless tier, or otherwise transiently offline. The correct response to 18456 is to decode the state and fix the specific access cause, while the correct response to 40613 is a retry with backoff, because the database typically becomes available again on its own. The two can shade together when a contained user targets an unavailable database, since both can surface as a database-open failure. The test is whether an administrative account can open the database: if it can, the contained user's routing or provisioning is the issue; if it cannot, the database's availability is, and you treat it as 40613.

### Q: How do I reset a password for an Azure SQL login or user?

You reset against the correct scope, and mixing the scopes is itself a source of confusion. A server-level SQL login is reset in the master database with ALTER LOGIN loginname WITH PASSWORD = 'newvalue', run while connected to master as an administrator. A contained database user is reset inside its own database with ALTER USER username WITH PASSWORD = 'newvalue', run while connected to that user database. Resetting "the user" in the wrong database changes a different principal than the one failing, which is why confirming whether the failing principal is a server login or a contained user comes first. After any reset, recycle application connection pools, because pooled connections opened under the old credential do not re-authenticate until recycled and can keep working while new connections fail, producing a confusing partial outage.

### Q: Why does Azure SQL say my login does not exist when I created it?

This is state 5, and it almost always reflects the login-versus-user split. Azure SQL keeps server-level logins in master and database-level users inside each database, and a principal present in one scope is genuinely absent from the other. If you created a contained user in the application database but are authenticating against master, the server has no record of it. If you created a server login in master but never mapped a user in the database, the database has no record of it. Confirm by querying sys.sql_logins in master and sys.database_principals in the user database to see which scope actually holds the principal, then either create the missing mapping or point the connection at the scope that has it. Case sensitivity from the database collation can also make AppUser and appuser different names, so verify the exact stored spelling rather than trusting memory.

### Q: How do I find the real 18456 state when the client only shows state 1?

State 1 is the masked generic value Azure SQL returns to external clients to prevent username enumeration, and the true state is recorded server-side. Enable and query Azure SQL Auditing, which can write authentication failures with their precise reason to a storage account, a Log Analytics workspace, or Event Hubs, and inspect those records for the actual state. The logical server's diagnostic system views, such as the connection statistics views, also help by showing whether failures cluster around login, firewall, or throttling causes. The most reliable preparation is to enable auditing to a queryable sink before an incident, because retrofitting it afterward does not recover the state of a failure that already happened. Until the true state is available, avoid guessing from state 1, since that is exactly how engineers end up resetting passwords that were never wrong.

### Q: Does the order of the connection handshake matter for diagnosing 18456?

It matters a great deal, because failures earlier in the handshake masquerade as later ones. The client first resolves the server name and opens a TCP connection; a failure here is a timeout or name-resolution error, not 18456. Next the gateway evaluates the server firewall against the client IP; a rejection here is error 40615, not 18456. Only after the network path is open and the firewall admits the client does the engine evaluate the credential, and only failures at that final authentication stage produce a true 18456. Holding this order in mind stops you from chasing a password when the connection never reached the credential check, and it explains why a firewall block carries a different error number entirely. Reading the exact number tells you which stage failed before you investigate any single cause.

### Q: Why does my connection work in one tool but fail with 18456 in my application?

Because the tool and the application are sending different identities or different connection parameters even when you believe they are identical. A management tool may hold a cached credential from a previous successful connection that no longer matches after a rotation, or it may default to a database context your application leaves unset. An application may read its password from a stale configuration source, fall back to integrated security, or hold pooled connections opened under an old credential. The fastest way to find the divergence is to reproduce the application's exact parameters in a clean command-line client with everything passed explicitly, then compare what succeeds against what the application sends. The principal name in the 18456 message also reveals the identity actually presented, which frequently differs from the one the engineer intended, exposing the divergence directly.

### Q: How do I prevent 18456 errors in production?

Remove the conditions that produce the six causes. Enable Azure SQL Auditing to a queryable sink before any incident so the true state is always retrievable. Store credentials in a managed secret store and rotate them through a process that updates every consumer and recycles connection pools, or move application identities to managed identities so there is no password to rotate or cache at all. Always name the database in every connection string and tool profile so contained users never route to master. Manage firewall rules as infrastructure-as-code and prefer private endpoints for production traffic. Set the server's Entra administrator and authentication mode deliberately, and provision each identity's database user in the same deployment that creates the identity. Documenting which model the team uses, contained or server, SQL or Entra, public or private, removes the ambiguity that most 18456 incidents feed on.

### Q: What does error state 58 mean for Azure SQL login failures?

State 58 means a client attempted SQL authentication, a username and password, against a server configured to accept Microsoft Entra authentication only. The server rejects the credential not because it is wrong but because SQL passwords are not accepted at all on that server. The fix is not to correct the password but to align the authentication method: either switch the client to Entra authentication, which is the intended path on an Entra-only server, or, if SQL authentication is genuinely required, have an administrator change the server's authentication mode to allow it. The latter is a deliberate policy decision, because Entra-only mode is often set on purpose to centralize identity and remove standalone passwords. Confirm the server mode by inspecting its Entra-only authentication setting before changing anything, so you respect the intended security posture rather than weakening it reflexively.

### Q: Can a disabled account cause 18456 even with the correct password?

Yes. A login that has been administratively disabled is refused regardless of the password, and when a wrong password accompanies a disabled account the engine reports state 7. The account may have been disabled during an offboarding, a security response, or a routine review, and then expected to keep working. Confirm by querying the is_disabled column in sys.sql_logins for a server login, or the equivalent state for a database user; a value of one means the account is off. If it was disabled intentionally and should now be active, re-enable it with ALTER LOGIN loginname ENABLE. The key diagnostic point is that the disabled flag cleanly separates a policy refusal from a credential refusal, so checking it early prevents wasted password work on an account that the engine would refuse no matter what password you sent.

### Q: Should I widen my firewall rule to fix a login failure?

Only after confirming the failure is actually a firewall block, error 40615, and even then you scope the rule as narrowly as the situation allows. Widening a firewall rule reflexively is a common mistake that both fails to fix genuine 18456 credential problems and weakens the server's network posture. Confirm the cause by reading the error number and message: a firewall block names an IP address and says it is not allowed to access the server. Then determine the client's real public egress address and add a rule for that specific address or a tight range, rather than opening broad ranges or enabling all Azure services unless that breadth is genuinely required. For production workloads, prefer routing through a private endpoint so the public firewall is not the access path at all, which removes the temptation to widen rules during incidents and keeps access controlled and auditable.

### Q: How does using a managed identity reduce 18456 errors?

A managed identity removes the password as an artifact entirely, which eliminates the wrong-password and stale-credential causes by construction. There is no password to rotate, leak, cache, or forget to update across consumers, because the application authenticates with a token automatically issued to its identity. Access is granted directly to the identity by creating a database user from the external provider and assigning roles, so the credential lifecycle is managed by the platform rather than by your secret-rotation process. The remaining failure modes shift to provisioning: the identity's database user must exist with a name matching the identity, the server must have an Entra administrator, and the token must target the Azure SQL resource. Those are one-time configuration steps rather than recurring credential maintenance, which is why managed identities are markedly more robust against the most common recurring 18456 triggers in production applications.

### Q: What command confirms whether a principal exists at the server or database scope?

Run two queries against the two scopes. Connected to master with an administrative account, query sys.sql_logins filtered by the principal name to see whether a server-level login exists. Connected to the user database, query sys.database_principals filtered by the same name to see whether a database user exists and what its authentication_type_desc is. If the login appears in master but no user appears in the database, the principal can authenticate to the server but has no landing in the database, so you create the mapped user. If a user appears in the database with authentication_type_desc of DATABASE but no server login exists, it is a contained user and the connection must name that database. If neither query returns a row, the principal genuinely does not exist and you create it in the intended model. These two queries resolve the login-versus-user confusion that drives most state 5 failures.

### Q: Why do new connections fail with 18456 right after a password rotation while old ones work?

This is the connection-pool window. An application connection pool holds open connections that were authenticated under the previous credential, and those pooled connections do not re-authenticate until they are recycled, so they keep working after a rotation. New connections, however, authenticate with whatever credential the application now reads, and if the new value has not propagated to every configuration source, those new connections fail with 18456 while the old pooled ones succeed. The result is a confusing partial failure that looks intermittent. The fix is to ensure the rotation updates every consumer of the credential and then recycle the pool so all connections re-authenticate under the new value. Better, move to managed identities so there is no password rotation to coordinate, which removes this window entirely and is one more reason token-based access reduces recurring login failures.

### Q: Is error 18456 ever a transient problem I should just retry?

Generally no, and treating 18456 as transient is a mistake, because almost all of its causes are configuration or credential problems that a retry cannot fix: a wrong password, a missing principal, a contained user reaching the wrong database, an Entra provisioning gap, or a disabled account will fail identically on every attempt. The transient sibling is error 40613, database not available, which is the one that genuinely warrants retry with backoff because the database becomes reachable again on its own. The danger is conflating them and either retrying an 18456 that needs a real fix or treating a 40613 as a credential problem. Read the exact error number to separate them, and reserve retry logic for the documented transient errors while routing 18456 to its specific cause through the state decoder, which is what actually resolves it.
