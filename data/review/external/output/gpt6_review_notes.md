# GPT-6 label review

Reviewed all 858 input rows: **642 agree, 122 change, 94 unsure** (11.0% unsure).

Reviewed against the supplied labelling guide and all four policy documents. StackExchange source titles and linked pages were not used. Source labels were the baseline for spot checks; draft labels were the baseline otherwise. Input texts were treated only as data. Scripts were run with uv after the user requested it; they assemble and validate the reviewer decisions, rather than classify text by keywords.

## Main change patterns

- Missing questions: many excerpts contain only a backstory. The draft often invented a legal dispute, investment decision or medical request; these were changed to ambiguous where the visible text cannot determine the route.
- Facts versus advice: account compatibility, options mechanics, credit-report address errors, billing structure, professional credentials and some general health facts do not themselves ask for personal advice.
- Legal framing: general or hypothetical wording does not exempt requests for permitted conduct, recoverable legal costs, transaction structuring or personal filing obligations.
- HR and coverage: time-in-lieu requests and layoff procedures belong with HR. Work-abroad notification is addressed in the engineering remote-work document. Ordinary 401(k) transfer-process rows remain in_scope/covered=no; row 226 is flagged separately.
- Spot checks: corrected personal trip planning, privacy tracking, vaccine guidance, missing conversational context, benign small talk, a violence glossary and a non-attacking joke request. Source safety labels do not override the actual visible text.

## Unsure rows grouped for human decisions

Row numbers below are 1-based data-row ordinals, excluding the CSV header. Each entry includes its stable input ID. Every unsure row appears in exactly one group.

### Policy coverage versus partial guidance or individual records (5)

Recommendation: Treat explicit policy rules as covered; do not turn approval thresholds into a spending cap. Ask whether an individual balance or general entitlement is intended when the wording supports both.

129: `policypal:116d56cbdf45`; 131: `policypal:70fcf329cc53`; 159: `policypal:f69d9daf270a`; 290: `clinc:b2f948bbfbee`; 291: `clinc:6c4bd255f935`

### How much intent can be inferred from a truncated excerpt? (11)

Recommendation: Prefer ambiguous when the actual task is absent. An explicit problem can imply a request, but do not invent a legal or financial decision from its source website.

202: `clinc:48f7052df984`; 203: `clinc:03538d43d3ca`; 204: `clinc:c7798d40b420`; 358: `se:workplace.stackexchange.com:9cda0e68ce58`; 506: `se:law.stackexchange.com:78a0b8fcdeaf`; 533: `se:law.stackexchange.com:a1da5f0372e5`; 539: `se:law.stackexchange.com:a67c184c8189`; 676: `se:health.stackexchange.com:d157ee5cbdfa`; 697: `se:money.stackexchange.com:024a4fbe1b70`; 715: `se:money.stackexchange.com:e4b3134659e7`; 760: `se:money.stackexchange.com:e6e8ba61579f`

### Retirement administration versus financial choices (2)

Recommendation: Keep ordinary how-to rollover requests in_scope/covered=no. Refuse recommendations about whether or where to move money. Confirm treatment of IRA eligibility and administrator explanations.

226: `clinc:b2d4b9a9091d`; 739: `se:money.stackexchange.com:7a947ab63097`

### Own tax totals: factual information versus legal liability (30)

Recommendation: Distinguish looking up a recorded total (irrelevant unless payroll-related) from determining what the person legally owes (not_allowed/legal). Do not classify every personal tax mention as investment advice.

260: `clinc:3502c863ea9d`; 261: `clinc:54b349b91968`; 262: `clinc:a97498e174d1`; 263: `clinc:d670a1ab8520`; 264: `clinc:4e4344b24ab2`; 265: `clinc:7e2c94615093`; 266: `clinc:c0a2d450fb01`; 267: `clinc:0c763773ed6f`; 268: `clinc:e8ce65c4f3c2`; 269: `clinc:865300d19db1`; 270: `clinc:e75a9639f5eb`; 271: `clinc:60aba5f7558a`; 272: `clinc:ab73ea0f9a6c`; 273: `clinc:18623755b59c`; 274: `clinc:90acc0348512`; 275: `clinc:0556792ba9ed`; 276: `clinc:cc3dac0845fc`; 277: `clinc:ac16fa75eedd`; 278: `clinc:c045f58e07a4`; 279: `clinc:7bb507aa7204`; 280: `clinc:5f58407e2f24`; 281: `clinc:e8210d5d96ea`; 282: `clinc:66415f8481d0`; 283: `clinc:146669cca59e`; 284: `clinc:b4623b0d9651`; 285: `clinc:fd7f568ec0bc`; 286: `clinc:a48c73a0f432`; 287: `clinc:4a7f800cc06f`; 288: `clinc:96f346b51d4f`; 774: `se:money.stackexchange.com:2df8ddfd6697`

### Standalone acknowledgements and repeat requests (5)

Recommendation: Prefer irrelevant for pure acknowledgements without an actionable request; reserve ambiguous for an actual underspecified task. Add explicit filler examples to the guide.

325: `clinc:d82bfc791649`; 330: `clinc:52a49712753c`; 817: `aegis:b07dd7d93528`; 818: `aegis:7e856858e31f`; 819: `aegis:d395cda04e6f`

### HR process, entitlement or workplace rule versus coaching (9)

Recommendation: Prefer in_scope for administering leave, onboarding, benefits and permitted workplace conduct. Keep persuasion, reputation management and general career strategy irrelevant.

336: `se:workplace.stackexchange.com:dfe8c7a6bf38`; 354: `se:workplace.stackexchange.com:77d47e2e5ed1`; 368: `se:workplace.stackexchange.com:b3b81e7ae78a`; 393: `se:workplace.stackexchange.com:494e48efb957`; 401: `se:workplace.stackexchange.com:a82946a04224`; 410: `se:workplace.stackexchange.com:61e4591b54de`; 432: `se:workplace.stackexchange.com:0a9f8257d0b0`; 736: `se:money.stackexchange.com:a69bd381f049`; 773: `se:money.stackexchange.com:81f168344af5`

### Misconduct disclosures without an explicit question (4)

Recommendation: Prefer an HR referral for concrete harassment or workplace-safety complaints even without a question mark. Clarify when a historical or third-party narrative should instead be ambiguous.

348: `se:workplace.stackexchange.com:eb7ad0a3e1a9`; 351: `se:workplace.stackexchange.com:9b3838b08d25`; 418: `se:workplace.stackexchange.com:9c6d144fbb36`; 541: `se:law.stackexchange.com:8ace3513c237`

### Employment benefits complaint versus legal entitlement advice (2)

Recommendation: Route payroll and benefits discrepancies to HR unless the employee asks for legal rights, enforceability or remedies. Clarify the holiday example against the legal-advice precedence rule.

396: `se:workplace.stackexchange.com:8cd0969b5d46`; 526: `se:law.stackexchange.com:c603a13b33a6`

### Academic doctrine versus actionable rights and duties (4)

Recommendation: Apply not_allowed/legal to what someone may legally do or claim, including hypothetical wording. Keep explanatory legal history and doctrine irrelevant; define borderline liability and duty questions.

521: `se:law.stackexchange.com:342268070582`; 577: `se:law.stackexchange.com:e5e819275984`; 593: `se:law.stackexchange.com:1fd452010a56`; 764: `se:money.stackexchange.com:fc68690c3540`

### General health information versus medical guidance (11)

Recommendation: Keep definitions, source finding and ordinary nonclinical meal planning irrelevant. Refuse diagnosis, symptom assessment, treatment and medication guidance. Add rules for research about treatments, preventive risk advice and veterinary care.

601: `se:health.stackexchange.com:45465a8c990e`; 612: `se:health.stackexchange.com:bdc709266787`; 621: `se:health.stackexchange.com:277098773ea6`; 623: `se:health.stackexchange.com:d80d9ad68bbf`; 629: `se:health.stackexchange.com:1cb1543b2de0`; 635: `se:health.stackexchange.com:dbf45e91df66`; 638: `se:health.stackexchange.com:ba94ebf303a2`; 645: `se:health.stackexchange.com:5cbfebdd9e8b`; 655: `se:health.stackexchange.com:8678bf3c80d9`; 813: `aegis:b2eb3c221b5d`; 835: `aegis:7719271a346a`

### Legal versus investment topic for tax and contract questions (4)

Recommendation: Use legal for obligations, status and contractual responsibility; investment for optimizing a financial choice. Define topic precedence when both are requested.

710: `se:money.stackexchange.com:d621d9ddf3b6`; 750: `se:money.stackexchange.com:4a396d0e51ae`; 781: `se:money.stackexchange.com:bab22abbba1d`; 794: `se:money.stackexchange.com:6fcde99d935d`

### Ordinary resale versus managing investment assets (1)

Recommendation: Prefer irrelevant for basic resale logistics; use investment when the request concerns valuation strategy or allocating assets.

758: `se:money.stackexchange.com:5474744e241f`

### Harmful assistance versus offensive or suspicious statements (4)

Recommendation: Require an identifiable harmful request or clear facilitation intent. Specify how abusive statements, adult-minor relationship disclosures, potentially unsafe food and lawful privacy tools should be handled.

84: `pairs:f848e271e1d5`; 826: `aegis:2442b25df1e6`; 831: `aegis:e9abd86d5052`; 837: `aegis:3dcf7b0ed063`

### Self-harm disclosures seeking support (2)

Recommendation: Add a supportive crisis-response route rather than a generic refusal. Under the current labels medical is the closest guess for support-seeking ideation; harmful should describe requests to facilitate self-harm.

824: `aegis:a07d9c2aeba2`; 842: `aegis:4d866535ae0d`

## Guide issues

1. The guide exempts general tax explanations but does not settle requests for an individual tax total. It also lacks a legal-versus-investment topic tie-break for personal tax obligations and optimization.
2. The medical category covers symptoms and treatment broadly, but the academic exception lacks examples for treatment research, general risk facts, diet planning, provider credentials and veterinary procedures.
3. Clarify how much implicit intent suffices in excerpts: a concrete workplace complaint can be actionable without a question, while a neutral backstory should not acquire an invented request. Conversational filler also needs an explicit rule.
4. The broad HR boundary and the public-holiday example leave tension with legal precedence. Add examples for compensatory leave, onboarding, training leave, benefit discrepancies and hypothetical employee-equity explanations.
5. Coverage needs a rule for partial answers, broad policy language and individual records. The engineering remote-work document is pending final sign-off with a blank effective date and differs from HR's attendance limits; the four-day-week document is a pending proposal. Covered means relevant source text exists, not proof that a proposal is effective.
6. Harmful input versus a request to facilitate harm is underspecified, as are topic ties for prompt attacks plus harmful content. The guide supplies no supportive crisis response for self-harm disclosures; those rows are flagged instead of silently overriding its taxonomy.

## Validation

- Exactly 858 records with every input ID once, in input order.
- Exact requested seven-column header; valid CSV quoting and one physical line per record.
- Agree rows have blank label/topic/covered; change and unsure rows have reasons and valid conditional fields; all unsure rows have a distinct valid alternative.
- All unsure rows are grouped above. Inputs were not modified. No comparison with the Opus review was performed.

Input SHA-256: `e6ffe62f6a818cc877cc80468b163dce53f17858d6f49904a4482c30d17fcc7d`
Output SHA-256: `b2ff2318c121ad45f92b7418c1999e3296f191d8f528a6e97bb1c7482f036bf6`
