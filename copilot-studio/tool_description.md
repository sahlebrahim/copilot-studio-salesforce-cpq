# soql tool description

this is the text that went into the "description for ai" field on the
salesforce "execute a soql query" tool, with the soql query input set to
fill with ai.

it's here as a record, not as working config. in this build nothing in
that field reached the model. the same field list now lives in
`instructions.md`, where it works.

if you're reproducing this project, put the field list in the agent
instructions and treat this file as a note on what didn't work.

## what was in the field

```
run a soql query against salesforce cpq data and return the rows. use this
for every question about opportunities, quotes, quote lines, accounts or
products.

objects and exact api field names:

Opportunity: Name, StageName, CloseDate, Amount, Account.Name
Account: Name, Industry

SBQQ__Quote__c:
  Name (the quote number, e.g. Q-00058), SBQQ__Status__c, SBQQ__Primary__c,
  SBQQ__Type__c, SBQQ__NetAmount__c, SBQQ__ListAmount__c,
  SBQQ__CustomerAmount__c, SBQQ__RegularAmount__c,
  SBQQ__AverageCustomerDiscount__c, SBQQ__LineItemCount__c,
  SBQQ__ExpirationDate__c, SBQQ__StartDate__c, SBQQ__EndDate__c,
  SBQQ__SubscriptionTerm__c, SBQQ__DaysQuoteOpen__c,
  SBQQ__Account__r.Name, SBQQ__Opportunity2__r.Name, SBQQ__SalesRep__r.Name

SBQQ__QuoteLine__c:
  SBQQ__Quote__r.Name, SBQQ__Product__r.Name, SBQQ__ProductName__c,
  SBQQ__ProductCode__c, SBQQ__ProductFamily__c, SBQQ__Quantity__c,
  SBQQ__ListPrice__c, SBQQ__NetPrice__c, SBQQ__ListTotal__c,
  SBQQ__NetTotal__c, SBQQ__Discount__c, SBQQ__TotalDiscountRate__c,
  SBQQ__TotalDiscountAmount__c, SBQQ__UnitCost__c, SBQQ__GrossProfit__c,
  SBQQ__Bundled__c, SBQQ__Optional__c, SBQQ__ChargeType__c,
  SBQQ__Number__c, SBQQ__StartDate__c, SBQQ__EndDate__c

notes:
- the opportunity lookup on a quote is SBQQ__Opportunity2__c, traversed as
  SBQQ__Opportunity2__r. do not use SBQQ__Opportunity__c; it does not exist.
- the child relationship from a quote to its lines is SBQQ__LineItems__r.
  do not use SBQQ__QuoteLines__r.
- quote status values: Draft, In Review, Approved, Denied, Presented,
  Accepted, Rejected.
- percent fields are whole numbers: 15 means 15 percent.
- SBQQ__UnitCost__c is the cost per unit and SBQQ__GrossProfit__c is the
  gross profit amount on a line.
- SBQQ__Cost__c on a quote line is a lookup to a Cost record, not a number.
- quotes on the same opportunity are alternative versions of one deal. never
  sum their amounts, discounts or margins together.
- bundled lines (SBQQ__Bundled__c = true) are priced at zero.
- select only the fields needed, and add limit 50 unless more are asked for.

(the full version also had the example query patterns that now sit in
instructions.md)
```

## how we found out it was inert

the text above was saved, showed in the tool details pane, and expanded in
full when clicked. the agent behaved as though none of it was there:

- 4 to 6 tool calls per question, most of them spent on schema discovery
  against EntityDefinition, FieldDefinition and `SELECT FIELDS(ALL)`
- a 400 error from guessing the standard `Quote` object with `GrandTotal`
  and `Status`, in 3 separate runs
- SBQQ__UnitCost__c and SBQQ__GrossProfit__c never used once, despite both
  being listed. it traversed SBQQ__Cost__r instead and at one point guessed
  a field called SBQQ__NetCost__c
- SBQQ__NetPrice__c returned for "show me the line items" when the note said
  to use SBQQ__NetTotal__c
- bundled lines priced at zero included in below cost answers, when the note
  said to exclude them

the test that settled it:

> what fields are available on the quote line object according to your
> instructions?

it summarised the instructions box correctly. list amount, net amount, whole
number discount percents, bundled lines priced at zero. then:

> The instructions do not provide a field list for the Quote Line object,
> and they do not specify any Quote Line field API names.

in another run it went further and ran `SELECT FIELDS(ALL) FROM
SBQQ__QuoteLine__c LIMIT 1` to answer the question, then listed the fields
"according to Salesforce", including the SBQQ__UnitCost__c and
SBQQ__GrossProfit__c it had failed to find earlier.

so the instructions box reaches the model. this field doesn't.

## the description you can't remove

copilot studio attaches its own description to every tool call, and there's
no way to turn it off:

> Executes a raw SOQL query against Salesforce. Object and field API names
> are org-specific and must not be guessed: call GetTables to list the
> objects available in this org, then call GetTable on the target object to
> get its exact field API names, before composing the query.

`GetTables` and `GetTable` aren't available in this agent. the model read
that, said in its own reasoning that it couldn't do what it was being told
to do, and improvised schema discovery instead.

so the guidance that did reach the model was wrong for this setup, and the
guidance that would have helped never arrived.

that's the clearest argument for building the same thing in code. there the
tool schema is the contract, nothing else is competing with it, and there's
no GetTables to go looking for.