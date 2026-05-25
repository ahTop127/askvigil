-- ==========================================
-- 1. 插入 20 条 Job Scams 的测试场景 (使用 1001-1020 作为起始 ID)
-- ==========================================
INSERT INTO quiz_questions (id, category_id, scenario_text, explanation) VALUES
-- 诈骗场景 (15个)
(1001, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'You receive a WhatsApp message from an unknown number offering you $200 a day to simply "like" YouTube videos.', 
 'This is a classic Task Scam. Legitimate companies do not recruit via unsolicited WhatsApp messages for simple, high-paying tasks. They use this to build initial trust before asking you to deposit your own money.'),

(1002, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'A recruiter offers you a remote job immediately after a brief text chat on Telegram. They never ask for a voice or video call.', 
 'Scammers often avoid voice or video calls to hide their identity and location. A legitimate company will always conduct proper interviews before hiring.'),

(1003, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'The company sends you a large check to buy a "home office setup", but asks you to wire a portion of the money to their "approved IT vendor".', 
 'This is a Fake Check Scam. The check they sent will eventually bounce, and the money you wired to the "vendor" (who is actually the scammer) will be lost from your own account.'),

(1004, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'An employer asks for your bank account login credentials so they can "set up your direct deposit" for your salary.', 
 'No legitimate employer will ever ask for your bank login password or username. They only need your routing and account numbers, typically provided through a secure HR portal.'),

(1005, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'You are offered an online data entry job, but you must pay a $50 "registration and training fee" before you can start working.', 
 'This is an Advance Fee Scam. You should never have to pay your employer to get a job. Legitimate training costs are covered by the company.'),

(1006, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'A supposed HR manager from Amazon emails you a job offer from "hr-amazon-careers@gmail.com".', 
 'Legitimate corporate recruiters will always use the official company domain (e.g., @amazon.com), never generic email services like Gmail, Yahoo, or Hotmail.'),

(1007, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'The job description requires you to receive packages at your home address and reship them to an overseas address.', 
 'This is a Parcel Mule Scam. You are being used to move stolen goods. If caught, you could face criminal charges for receiving stolen property.'),

(1008, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'A recruiter contacts you and urgently demands your Social Security Number and a photo of your ID before even scheduling an interview.', 
 'This is an Identity Theft attempt. While employers need this info eventually for background checks and taxes, it is never required before a formal interview and job offer.'),

(1009, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'You apply for a job, and they require you to download a "company secure messaging app" via an unknown APK link instead of the official App Store.', 
 'Downloading apps from unverified links or APKs can install malware on your device, allowing scammers to steal your personal data or banking information.'),

(1010, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'You are hired as a "Financial Agent". Your only duty is to receive funds into your personal bank account and transfer them to a cryptocurrency wallet.', 
 'This is a Money Mule Scam. Scammers are using your account to launder stolen money. This is highly illegal and your bank account will likely be frozen.'),

(1011, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'A job platform requires you to deposit USDT (cryptocurrency) to "unlock higher tier tasks" to earn more commission.', 
 'This is a Ponzi-style Task Scam. The platform will trap your crypto, and eventually, you will not be able to withdraw any of your "earnings" or original deposit.'),

(1012, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'You are pressured to sign a contract and provide personal details immediately, with the recruiter stating the offer "expires in 30 minutes".', 
 'Scammers use artificial urgency to force you into making rash decisions without doing proper research. Legitimate offers give you time to read and consider.'),

(1013, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'An "HR Manager" reaches out on LinkedIn. However, their profile has no picture, zero connections, and was created yesterday.', 
 'A brand new, empty LinkedIn profile claiming to be an established HR manager is a massive red flag indicating a fake account created solely for scamming.'),

(1014, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'The job requires you to purchase products on Amazon with your own money to leave 5-star reviews, promising to reimburse you later.', 
 'This is a Brushing Scam. Not only does it violate platform policies, but scammers often disappear without ever reimbursing you for the expensive products you bought.'),

(1015, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'You are asked to pay for your own background check through a specific, unknown website link provided by the recruiter.', 
 'Legitimate companies cover the cost of background checks. If you pay through their link, they steal both your money and your sensitive personal information.'),

-- 合法/安全场景 (5个 - 锻炼用户的辨别能力)
(1016, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'After applying on a company website, HR emails you from their corporate email address to schedule a Zoom video interview.', 
 'This is a standard and safe hiring process. The communication is via a verified corporate domain, and they are setting up a face-to-face (video) evaluation.'),

(1017, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'You accept a remote job offer after three rounds of interviews. The company says they will ship a laptop and monitor directly to your house at their expense.', 
 'This is safe. Legitimate remote companies handle the procurement and shipping of equipment themselves, without asking you to buy it upfront or cash a check.'),

(1018, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'A local retail store calls you after you submitted a paper application. They ask you to come in for an in-person interview tomorrow.', 
 'This is a perfectly normal hiring practice for local businesses. You applied directly, and they want to meet you in person without requesting any fees or sensitive data.'),

(1019, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'A recruiter on LinkedIn messages you about a role. Their profile shows 500+ connections, history with the company, and they invite you to apply on the official company careers page.', 
 'This is a legitimate recruitment strategy. A well-established profile directing you to an official, verifiable company website is safe.'),

(1020, (SELECT id FROM scam_categories WHERE name = 'Job Scams' LIMIT 1), 
 'After signing your employment contract, HR sends you a link to a well-known, secure payroll portal (like Workday or ADP) to enter your tax and banking details.', 
 'This is standard onboarding. Providing banking details through a secure, recognized third-party payroll system after formal hiring is normal and required for you to get paid.');


-- ==========================================
-- 2. 插入对应的选项 (每个问题2个选项，ID 2001-2040)
-- ==========================================
INSERT INTO quiz_options (id, question_id, option_text, is_correct) VALUES
-- Q1001 (Scam)
(2001, 1001, 'It''s a scam', TRUE),
(2002, 1001, 'No, it''s safe', FALSE),

-- Q1002 (Scam)
(2003, 1002, 'It''s a scam', TRUE),
(2004, 1002, 'No, it''s safe', FALSE),

-- Q1003 (Scam)
(2005, 1003, 'It''s a scam', TRUE),
(2006, 1003, 'No, it''s safe', FALSE),

-- Q1004 (Scam)
(2007, 1004, 'It''s a scam', TRUE),
(2008, 1004, 'No, it''s safe', FALSE),

-- Q1005 (Scam)
(2009, 1005, 'It''s a scam', TRUE),
(2010, 1005, 'No, it''s safe', FALSE),

-- Q1006 (Scam)
(2011, 1006, 'It''s a scam', TRUE),
(2012, 1006, 'No, it''s safe', FALSE),

-- Q1007 (Scam)
(2013, 1007, 'It''s a scam', TRUE),
(2014, 1007, 'No, it''s safe', FALSE),

-- Q1008 (Scam)
(2015, 1008, 'It''s a scam', TRUE),
(2016, 1008, 'No, it''s safe', FALSE),

-- Q1009 (Scam)
(2017, 1009, 'It''s a scam', TRUE),
(2018, 1009, 'No, it''s safe', FALSE),

-- Q1010 (Scam)
(2019, 1010, 'It''s a scam', TRUE),
(2020, 1010, 'No, it''s safe', FALSE),

-- Q1011 (Scam)
(2021, 1011, 'It''s a scam', TRUE),
(2022, 1011, 'No, it''s safe', FALSE),

-- Q1012 (Scam)
(2023, 1012, 'It''s a scam', TRUE),
(2024, 1012, 'No, it''s safe', FALSE),

-- Q1013 (Scam)
(2025, 1013, 'It''s a scam', TRUE),
(2026, 1013, 'No, it''s safe', FALSE),

-- Q1014 (Scam)
(2027, 1014, 'It''s a scam', TRUE),
(2028, 1014, 'No, it''s safe', FALSE),

-- Q1015 (Scam)
(2029, 1015, 'It''s a scam', TRUE),
(2030, 1015, 'No, it''s safe', FALSE),

-- Q1016 (Safe / Legitimate)
(2031, 1016, 'It''s a scam', FALSE),
(2032, 1016, 'No, it''s safe', TRUE),

-- Q1017 (Safe / Legitimate)
(2033, 1017, 'It''s a scam', FALSE),
(2034, 1017, 'No, it''s safe', TRUE),

-- Q1018 (Safe / Legitimate)
(2035, 1018, 'It''s a scam', FALSE),
(2036, 1018, 'No, it''s safe', TRUE),

-- Q1019 (Safe / Legitimate)
(2037, 1019, 'It''s a scam', FALSE),
(2038, 1019, 'No, it''s safe', TRUE),

-- Q1020 (Safe / Legitimate)
(2039, 1020, 'It''s a scam', FALSE),
(2040, 1020, 'No, it''s safe', TRUE);

-- ==========================================
-- 1. 插入 20 条 Phishing Scams 的测试场景 (使用 1021-1040 作为起始 ID)
-- ==========================================
INSERT INTO quiz_questions (id, category_id, scenario_text, explanation) VALUES
-- 诈骗场景 (15个)
(1021, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'You receive an SMS from "Pos Malaysia": Your package is held at our depot due to an unpaid shipping fee of RM 1.50. Pay here: pos-my-update.com', 
 'This is a Smishing (SMS Phishing) scam. Official postal services will not ask you to click unofficial links like "pos-my-update.com" to pay small fees.'),

(1022, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'An email from "Netflix" claims your membership is paused due to a billing error. The link directs you to netflix-billing-update.info to enter your credit card.', 
 'This is a classic credential harvesting scam. Legitimate companies use their official domains (e.g., netflix.com), not variations with ".info" or extra words.'),

(1023, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'You get an email from admin@paypal-support.com stating your account is limited. It asks you to download an attached PDF form to verify your identity.', 
 'Scammers often spoof email addresses. "paypal-support.com" is not the official PayPal domain. Opening unexpected attachments can install malware or lead to fake login pages.'),

(1024, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'An SMS alerts you: "Maybank: Your account has been flagged for suspicious activity. Secure your account now at bit.ly/mb2u-secure".', 
 'Banks never use link shorteners like bit.ly. This is designed to hide the true, malicious URL you are being sent to.'),

(1025, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'You receive an email from the "Tax Department (LHDN)" stating you have an unclaimed tax refund of RM 1,200. It includes a link to claim it by entering your bank login details.', 
 'Government tax agencies do not send unsolicited emails offering refunds, and they will NEVER ask for your bank account login credentials.'),

(1026, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'A friend direct messages you on Instagram: "Hey! I am in a photography contest. Can you vote for me by logging in to this link?"', 
 'Your friend''s account has likely been hacked. The link will take you to a fake Instagram login page designed to steal your password so they can hack you next.'),

(1027, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'An email warns you that your "Microsoft 365 password expires in 2 hours." It provides a link to "Keep same password here".', 
 'IT departments do not send emails offering to "keep the same password" via external links. This is a common tactic to steal corporate credentials.'),

(1028, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'You get a text message saying: "Your credit card was charged RM 4,500. If this was not you, call the fraud department immediately at the number below." You do not recognize the number.', 
 'This is a Vishing (Voice Phishing) setup. The number does not belong to your bank; it connects you directly to scammers who will ask for your card details to "cancel" the fake charge.'),

(1029, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'An urgent email from your "CEO" asks you to quickly review a secure contract link and sign in with your work email.', 
 'This is Spear-Phishing or CEO Fraud. Scammers impersonate executives to pressure employees into bypassing security checks and giving up login details.'),

(1030, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'You receive a notification that your Apple ID is locked. The email directs you to secure-apple-verify.net to unlock it.', 
 'Always check the URL. Official Apple communications will direct you to apple.com. Fake domains are a primary indicator of a phishing attempt.'),

(1031, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'An email from your internet provider says your latest bill payment failed and your service will be disconnected in 1 hour if you don''t pay via the provided link.', 
 'Scammers create extreme urgency (e.g., "disconnected in 1 hour") to make you panic and click the malicious link without thinking critically.'),

(1032, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'You receive a Google Doc shared by an unknown person. Clicking the link takes you to a page that requires you to enter your Google password to view the document.', 
 'If you are already logged into Google, you shouldn''t need to log in again just to view a document. This is a fake login overlay meant to steal your credentials.'),

(1033, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'An email claims your Spotify Premium payment failed. It looks identical to a real Spotify email, but the sender''s address is spotify@update-billing-info.com.', 
 'Even if the email design is perfectly copied, the sender''s email address reveals it''s a scam. Always expand and check the actual sender address.'),

(1034, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'You receive an urgent alert from a Cryptocurrency Exchange: "Withdrawal of 0.5 BTC requested. If this wasn''t you, cancel the transaction here: binance-cancel-req.com".', 
 'Scammers target crypto users because transactions are irreversible. The link leads to a fake exchange site that will steal your login and drain your wallet.'),

(1035, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'An email from "HR" announces a mandatory company policy update. You are instructed to download the attached ZIP file to read the new policy.', 
 'Unsolicited ZIP files, especially those claiming to be "mandatory updates" or "invoices," frequently contain ransomware or trojan viruses.'),

-- 合法/安全场景 (5个 - 锻炼用户的辨别能力)
(1036, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'You forgot your Instagram password and request a reset. Five seconds later, you receive an email from security@mail.instagram.com with a reset link.', 
 'This is safe. You initiated the action, you were expecting the email immediately, and the sender address is an official Instagram domain.'),

(1037, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'Your banking app sends a push notification: "Your monthly e-statement is ready. Please open the official app to view it." There are no links in the notification.', 
 'This is safe. The bank is not sending you a link to click; instead, they are correctly instructing you to navigate independently using your secure, official app.'),

(1038, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'You receive an email from an airline confirming a flight ticket you just purchased 10 minutes ago. All the flight details and booking references match perfectly.', 
 'This is a standard and safe transactional email. It correlates directly with an action you just performed, and the details are accurate.'),

(1039, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'Your university IT department sends an email reminding you that cybersecurity training is due. They tell you to go to the student portal via your browser bookmarks to complete it.', 
 'This is safe. Good IT departments encourage users to navigate to internal portals via bookmarks or known URLs rather than clicking direct links in emails.'),

(1040, (SELECT id FROM scam_categories WHERE name = 'Phishing Scams' LIMIT 1), 
 'A tech newsletter you subscribed to months ago sends its weekly digest. At the very bottom, there is a standard link that says "Unsubscribe from this list".', 
 'This is safe. Legitimate marketing emails are required by law to include an unsubscribe link at the bottom of their communications.');


-- ==========================================
-- 2. 插入对应的选项 (每个问题2个选项，ID 2041-2080)
-- ==========================================
INSERT INTO quiz_options (id, question_id, option_text, is_correct) VALUES
-- Q1021 (Scam)
(2041, 1021, 'It''s a scam', TRUE),
(2042, 1021, 'No, it''s safe', FALSE),

-- Q1022 (Scam)
(2043, 1022, 'It''s a scam', TRUE),
(2044, 1022, 'No, it''s safe', FALSE),

-- Q1023 (Scam)
(2045, 1023, 'It''s a scam', TRUE),
(2046, 1023, 'No, it''s safe', FALSE),

-- Q1024 (Scam)
(2047, 1024, 'It''s a scam', TRUE),
(2048, 1024, 'No, it''s safe', FALSE),

-- Q1025 (Scam)
(2049, 1025, 'It''s a scam', TRUE),
(2050, 1025, 'No, it''s safe', FALSE),

-- Q1026 (Scam)
(2051, 1026, 'It''s a scam', TRUE),
(2052, 1026, 'No, it''s safe', FALSE),

-- Q1027 (Scam)
(2053, 1027, 'It''s a scam', TRUE),
(2054, 1027, 'No, it''s safe', FALSE),

-- Q1028 (Scam)
(2055, 1028, 'It''s a scam', TRUE),
(2056, 1028, 'No, it''s safe', FALSE),

-- Q1029 (Scam)
(2057, 1029, 'It''s a scam', TRUE),
(2058, 1029, 'No, it''s safe', FALSE),

-- Q1030 (Scam)
(2059, 1030, 'It''s a scam', TRUE),
(2060, 1030, 'No, it''s safe', FALSE),

-- Q1031 (Scam)
(2061, 1031, 'It''s a scam', TRUE),
(2062, 1031, 'No, it''s safe', FALSE),

-- Q1032 (Scam)
(2063, 1032, 'It''s a scam', TRUE),
(2064, 1032, 'No, it''s safe', FALSE),

-- Q1033 (Scam)
(2065, 1033, 'It''s a scam', TRUE),
(2066, 1033, 'No, it''s safe', FALSE),

-- Q1034 (Scam)
(2067, 1034, 'It''s a scam', TRUE),
(2068, 1034, 'No, it''s safe', FALSE),

-- Q1035 (Scam)
(2069, 1035, 'It''s a scam', TRUE),
(2070, 1035, 'No, it''s safe', FALSE),

-- Q1036 (Safe / Legitimate)
(2071, 1036, 'It''s a scam', FALSE),
(2072, 1036, 'No, it''s safe', TRUE),

-- Q1037 (Safe / Legitimate)
(2073, 1037, 'It''s a scam', FALSE),
(2074, 1037, 'No, it''s safe', TRUE),

-- Q1038 (Safe / Legitimate)
(2075, 1038, 'It''s a scam', FALSE),
(2076, 1038, 'No, it''s safe', TRUE),

-- Q1039 (Safe / Legitimate)
(2077, 1039, 'It''s a scam', FALSE),
(2078, 1039, 'No, it''s safe', TRUE),

-- Q1040 (Safe / Legitimate)
(2079, 1040, 'It''s a scam', FALSE),
(2080, 1040, 'No, it''s safe', TRUE);

-- ==========================================
-- 1. 插入 20 条 OTP Scams 的测试场景 (使用 1041-1060 作为起始 ID)
-- ==========================================
INSERT INTO quiz_questions (id, category_id, scenario_text, explanation) VALUES
-- 诈骗场景 (15个)
(1041, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'You receive a text with a 6-digit code. Seconds later, a stranger messages you: "Sorry, I entered the wrong number by mistake. Could you please send me the code you just got?"', 
 'This is a classic WhatsApp/Telegram account takeover scam. The scammer is trying to log into an account using your phone number, and that code is YOUR login verification. Never share it.'),

(1042, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'A caller claiming to be from your bank says there is a fraudulent RM 2,000 charge on your card. To block it, they ask you to read the OTP they just sent to your phone.', 
 'Real banks will NEVER ask you to read an OTP over the phone to "block" a transaction. The scammer is actually initiating a transfer and needs your OTP to complete it.'),

(1043, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'Your friend messages you on Facebook: "Hey, my phone is broken and I''m trying to recover my account. I sent a recovery code to your number. Can you tell me what it is?"', 
 'Your friend''s Facebook account has already been hacked. The scammer is now trying to hack YOUR account, or use your number to set up a fraudulent account elsewhere.'),

(1044, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'A "Shopee customer service" agent calls to say your recent order is stuck. They say they will resend it, but you need to confirm the verification code sent via SMS.', 
 'Official e-commerce customer service will never need an OTP to resolve delivery issues. They are trying to log into your shopping account or authorize a payment.'),

(1045, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'You are selling a used phone on Carousell. The buyer says they want to "verify you are a real seller" and asks you to send them the 6-digit code you just received.', 
 'Buyers do not need to verify sellers using SMS codes. The "buyer" is actually using your phone number to register for a service or authorize a transaction.'),

(1046, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'A caller claiming to be from the police says your identity was used in a money laundering case. To prove your innocence and freeze your assets, you must provide the TAC code sent to you.', 
 'Law enforcement will never call to ask for a TAC/OTP. This is an impersonation scam designed to panic you into handing over access to your bank account.'),

(1047, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'You receive a message from your Telco (e.g., Maxis/Celcom) offering a free 50GB data upgrade. To activate it, you just need to reply to the SMS with the OTP you receive.', 
 'Telcos do not require OTPs to give you free upgrades. Scammers often spoof Telco sender IDs to steal codes that can authorize carrier billing charges.'),

(1048, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'A food delivery rider calls and says his app is glitching and he can''t see your location. He asks for the SMS code you just received so he can "refresh" the system.', 
 'Delivery apps do not require riders to manually enter customer OTPs to see locations. The rider might be trying to log into your account or authorize a charge.'),

(1049, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'You match with someone on a dating app. Before meeting up, they ask you to verify your identity by sending them a code from a "safety verification service" SMS.', 
 'This is a verification scam. The code is actually for a premium subscription or setting up an account using your phone number, and the person you matched with is a bot or scammer.'),

(1050, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'You get a pop-up saying your computer has a virus. You call the tech support number, and they ask for the OTP sent to your phone to "authenticate remote repair access".', 
 'Tech support scams use fake alerts. By giving them the OTP, you might be authorizing a payment for their "services" or giving them full control over your accounts.'),

(1051, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'A recruiter contacts you on Telegram offering a remote job. To complete the "onboarding profile," they ask you to forward the verification code sent from a payroll app.', 
 'Legitimate companies do not use Telegram to ask for OTPs for onboarding. They are setting up a financial account in your name to use as a money mule.'),

(1052, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'You receive a message on Instagram saying you won a giveaway. To claim the cash prize, the organizer says they need the security code sent to your phone number.', 
 'You cannot receive money via an OTP. The code is a password reset or login code for your social media or email account.'),

(1053, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'A caller claiming to be from the Inland Revenue Board (LHDN) says you overpaid taxes. To process the refund, you need to share the OTP sent to your mobile.', 
 'Government agencies never process refunds by asking for an OTP over the phone. They only credit verified bank accounts directly.'),

(1054, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'You receive an SMS from "TNG eWallet" saying your account will be suspended in 24 hours. The message includes a link, and the website asks you to enter your PIN and a new OTP.', 
 'This is a phishing site designed to steal your OTP. Always open the official app to check your account status, never click links in urgent SMS warnings.'),

(1055, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'Your "mom" messages you from a new number: "I lost my phone and got this new number. Can you send me RM 500? Also, I need to log into my email, send me the code that just went to your phone."', 
 'This is an impersonation scam. The scammer is trying to steal your money and simultaneously use your phone number as a recovery method to hack into accounts.'),

-- 合法/安全场景 (5个 - 锻炼用户的辨别能力)
(1056, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'You are buying a flight ticket online. On the payment page, it redirects to your bank''s secure 3D-Secure page. You receive an SMS TAC and enter it directly onto the webpage.', 
 'This is a safe and standard procedure. You initiated the transaction, you are on the bank''s secure payment gateway, and you are entering the code yourself, not giving it to a person.'),

(1057, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'You forgot your Gmail password. You click "Forgot Password" on the official Google login page, receive a verification code via SMS, and type it into the Google site.', 
 'This is safe. You requested the password reset yourself, and you are entering the code directly into the official service you are trying to access.'),

(1058, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'You buy a high-value item like a laptop on Lazada. The delivery driver arrives at your house, hands you the package, and asks you to read him the delivery OTP to complete the handover.', 
 'This is safe. Many e-commerce platforms now use delivery OTPs for expensive items to prevent theft. It is safe to give this specific delivery code to the driver in person.'),

(1059, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'You buy a new phone and install WhatsApp. When setting it up, WhatsApp sends you an SMS code, which you type into the app on your new phone.', 
 'This is safe. You are setting up your own device and entering the verification code directly into the official application.'),

(1060, (SELECT id FROM scam_categories WHERE name = 'OTP Scams' LIMIT 1), 
 'You are linking your bank account to an e-wallet (like GrabPay or TNG). The e-wallet app redirects to the bank''s login page, which sends an OTP to your phone to authorize the linkage.', 
 'This is safe. As long as you initiated the linking process within the official app and are entering the OTP on the verified bank portal, it is a legitimate security measure.');


-- ==========================================
-- 2. 插入对应的选项 (每个问题2个选项，ID 2081-2120)
-- ==========================================
INSERT INTO quiz_options (id, question_id, option_text, is_correct) VALUES
-- Q1041 (Scam)
(2081, 1041, 'It''s a scam', TRUE),
(2082, 1041, 'No, it''s safe', FALSE),

-- Q1042 (Scam)
(2083, 1042, 'It''s a scam', TRUE),
(2084, 1042, 'No, it''s safe', FALSE),

-- Q1043 (Scam)
(2085, 1043, 'It''s a scam', TRUE),
(2086, 1043, 'No, it''s safe', FALSE),

-- Q1044 (Scam)
(2087, 1044, 'It''s a scam', TRUE),
(2088, 1044, 'No, it''s safe', FALSE),

-- Q1045 (Scam)
(2089, 1045, 'It''s a scam', TRUE),
(2090, 1045, 'No, it''s safe', FALSE),

-- Q1046 (Scam)
(2091, 1046, 'It''s a scam', TRUE),
(2092, 1046, 'No, it''s safe', FALSE),

-- Q1047 (Scam)
(2093, 1047, 'It''s a scam', TRUE),
(2094, 1047, 'No, it''s safe', FALSE),

-- Q1048 (Scam)
(2095, 1048, 'It''s a scam', TRUE),
(2096, 1048, 'No, it''s safe', FALSE),

-- Q1049 (Scam)
(2097, 1049, 'It''s a scam', TRUE),
(2098, 1049, 'No, it''s safe', FALSE),

-- Q1050 (Scam)
(2099, 1050, 'It''s a scam', TRUE),
(2100, 1050, 'No, it''s safe', FALSE),

-- Q1051 (Scam)
(2101, 1051, 'It''s a scam', TRUE),
(2102, 1051, 'No, it''s safe', FALSE),

-- Q1052 (Scam)
(2103, 1052, 'It''s a scam', TRUE),
(2104, 1052, 'No, it''s safe', FALSE),

-- Q1053 (Scam)
(2105, 1053, 'It''s a scam', TRUE),
(2106, 1053, 'No, it''s safe', FALSE),

-- Q1054 (Scam)
(2107, 1054, 'It''s a scam', TRUE),
(2108, 1054, 'No, it''s safe', FALSE),

-- Q1055 (Scam)
(2109, 1055, 'It''s a scam', TRUE),
(2110, 1055, 'No, it''s safe', FALSE),

-- Q1056 (Safe / Legitimate)
(2111, 1056, 'It''s a scam', FALSE),
(2112, 1056, 'No, it''s safe', TRUE),

-- Q1057 (Safe / Legitimate)
(2113, 1057, 'It''s a scam', FALSE),
(2114, 1057, 'No, it''s safe', TRUE),

-- Q1058 (Safe / Legitimate)
(2115, 1058, 'It''s a scam', FALSE),
(2116, 1058, 'No, it''s safe', TRUE),

-- Q1059 (Safe / Legitimate)
(2117, 1059, 'It''s a scam', FALSE),
(2118, 1059, 'No, it''s safe', TRUE),

-- Q1060 (Safe / Legitimate)
(2119, 1060, 'It''s a scam', FALSE),
(2120, 1060, 'No, it''s safe', TRUE);

-- ==========================================
-- 1. 插入 20 条 QR Code Scams 的测试场景 (使用 1061-1080 作为起始 ID)
-- ==========================================
INSERT INTO quiz_questions (id, category_id, scenario_text, explanation) VALUES
-- 诈骗场景 (15个)
(1061, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'You park your car at a public parking spot and see a new, slightly misaligned QR code sticker plastered over the parking meter''s official payment instructions.', 
 'This is a classic physical QR code replacement scam. Scammers paste their own QR codes over legitimate ones to divert your parking payment directly into their accounts.'),

(1062, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'At a cafe, you notice the QR code on the table for ordering food is slightly peeling. Upon closer inspection, it is a sticker covering another QR code underneath.', 
 'Never scan a QR code sticker that has been placed over an original printed one. It will likely redirect you to a fake payment gateway designed to steal your credit card details.'),

(1063, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'You receive an email from "HR" about a mandatory new salary policy. Instead of a link or an attachment, the email only contains a large QR code for you to scan with your phone.', 
 'This is known as "Quishing" (QR Phishing). Scammers use QR codes in emails to bypass corporate security filters that normally scan text links for malicious websites.'),

(1064, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'You find a "parking violation" ticket on your car windshield. It looks official and instructs you to scan a QR code to pay a RM50 fine immediately to avoid being towed.', 
 'Fake parking tickets are a common scare tactic. Scanning the code takes you to a fake council website designed to steal your payment information.'),

(1065, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'To access free Wi-Fi at a shopping mall, you scan a promotional poster''s QR code. It prompts you to install an "APK profile" or application on your phone to connect.', 
 'Legitimate free Wi-Fi may require a web login, but it will never force you to download and install an APK or profile. This will install malware or spyware on your device.'),

(1066, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'Someone on a dating app asks to move the conversation to WhatsApp. Instead of giving their number, they send you a QR code and say, "Scan this with your WhatsApp to add me directly."', 
 'This is a WhatsApp Web login scam. By scanning it within WhatsApp, you are actually authorizing their computer to log into YOUR WhatsApp account.'),

(1067, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'You receive a physical postcard in your mailbox claiming a parcel is stuck at the PosLaju depot. You must scan the QR code to pay a RM 2.00 redelivery fee.', 
 'Postal services do not leave physical cards with QR codes for redelivery payments. The tiny fee is just bait to get you to enter your credit card details on a fake site.'),

(1068, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'You scan a static QR code at a night market (pasar malam) to pay for food. Instead of opening your e-wallet app, it opens your web browser and asks for your credit card details.', 
 'A legitimate merchant payment QR code (like DuitNow) will trigger your banking or e-wallet app. If it redirects to a website asking for card details, it is a phishing site.'),

(1069, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'You scan the QR code on an EV charging station. The payment site looks legitimate, but you notice the URL in your browser is misspelled (e.g., charge-station-my.com instead of the official brand).', 
 'Scammers often place fake QR codes on unattended kiosks like EV chargers, ATMs, or vending machines. Always double-check the URL before making a payment.'),

(1070, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'A promoter in a mall asks you to scan a QR code to fill out a 1-minute survey for a free power bank. The form requires your IC number, bank account number, and mother''s maiden name.', 
 'Scanning the code isn''t the danger here, but the destination is. A simple survey for a free gift should never require highly sensitive security questions and banking details.'),

(1071, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'A TikTok video promises free cryptocurrency. It shows a QR code on screen and tells you to scan it using your crypto wallet app to "connect and claim the airdrop funds."', 
 'Scanning QR codes with a crypto wallet can authorize a malicious smart contract. Once connected, the scammers can drain all the funds from your wallet.'),

(1072, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'You receive a letter that looks like it''s from the Police (PDRM) stating you have unpaid traffic summons. The only way to view the photo evidence is by scanning the included QR code.', 
 'Official government notices will provide a secure portal URL (like MyEG) for you to log into independently, not force you through a direct QR code to view "evidence."'),

(1073, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'You scan a QR code on a flyer for a "Buy 1 Free 1 Starbucks" promotion. The link directs you to a login page that asks for your Facebook username and password to "verify your identity."', 
 'This is a credential harvesting scam. Promotions rarely require you to log into your social media on a random third-party website.'),

(1074, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'You receive a printed flyer offering a special low-interest personal loan. Scanning the QR code opens a website that looks exactly like Maybank2u, asking for your username and password.', 
 'Banks do not distribute loan applications via QR codes on flyers that lead directly to a login page. This is a phishing site designed to steal your banking credentials.'),

(1075, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'A street fundraiser holds up a printed QR code asking for donations. When you scan it, the prompt in the payment app asks you to authorize a "Recurring Monthly Subscription" rather than a one-time payment.', 
 'Always read the prompt carefully after scanning. Scammers trick people into setting up recurring direct debits instead of a single donation.'),

-- 合法/安全场景 (5个 - 锻炼用户的辨别能力)
(1076, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'You are at a major supermarket checkout. The cashier selects "e-Wallet payment," and the digital screen facing you generates a unique, dynamic QR code for your specific bill amount.', 
 'This is safe. Dynamic QR codes generated in real-time on a merchant''s official POS system screen are highly secure and cannot be tampered with by physical stickers.'),

(1077, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'You visit a national museum. Next to a historical artifact, there is a printed QR code. Scanning it simply opens the museum''s official website (e.g., museum.gov.my) to display a text description.', 
 'This is safe. Educational QR codes that lead to official, verifiable domains without asking for personal information or downloads are the intended use of the technology.'),

(1078, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'You want to log into WhatsApp Web on your personal laptop. You navigate to web.whatsapp.com on your browser and use your phone''s official WhatsApp application to scan the code on your screen.', 
 'This is safe. You initiated the login, you verified the URL is the official web.whatsapp.com, and you are scanning your own screen, not a code sent by a stranger.'),

(1079, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'You sit down at an established restaurant. The waiter brings over a plastic standee with a QR code. Scanning it simply opens a PDF file of their food menu on your phone, without asking for login details.', 
 'This is safe and very common. As long as the QR code just displays a document or an informational webpage without requesting sensitive data, it is harmless.'),

(1080, (SELECT id FROM scam_categories WHERE name = 'QR Code Scams' LIMIT 1), 
 'To receive money from a friend who split the dinner bill, you open your banking app, generate your own personal "Receive Funds" QR code, and show your phone screen to your friend to scan.', 
 'This is safe. Generating a QR code from within your secure banking app for someone else to scan is the correct and safe way to receive peer-to-peer payments.');


-- ==========================================
-- 2. 插入对应的选项 (每个问题2个选项，ID 2121-2160)
-- ==========================================
INSERT INTO quiz_options (id, question_id, option_text, is_correct) VALUES
-- Q1061 (Scam)
(2121, 1061, 'It''s a scam', TRUE),
(2122, 1061, 'No, it''s safe', FALSE),

-- Q1062 (Scam)
(2123, 1062, 'It''s a scam', TRUE),
(2124, 1062, 'No, it''s safe', FALSE),

-- Q1063 (Scam)
(2125, 1063, 'It''s a scam', TRUE),
(2126, 1063, 'No, it''s safe', FALSE),

-- Q1064 (Scam)
(2127, 1064, 'It''s a scam', TRUE),
(2128, 1064, 'No, it''s safe', FALSE),

-- Q1065 (Scam)
(2129, 1065, 'It''s a scam', TRUE),
(2130, 1065, 'No, it''s safe', FALSE),

-- Q1066 (Scam)
(2131, 1066, 'It''s a scam', TRUE),
(2132, 1066, 'No, it''s safe', FALSE),

-- Q1067 (Scam)
(2133, 1067, 'It''s a scam', TRUE),
(2134, 1067, 'No, it''s safe', FALSE),

-- Q1068 (Scam)
(2135, 1068, 'It''s a scam', TRUE),
(2136, 1068, 'No, it''s safe', FALSE),

-- Q1069 (Scam)
(2137, 1069, 'It''s a scam', TRUE),
(2138, 1069, 'No, it''s safe', FALSE),

-- Q1070 (Scam)
(2139, 1070, 'It''s a scam', TRUE),
(2140, 1070, 'No, it''s safe', FALSE),

-- Q1071 (Scam)
(2141, 1071, 'It''s a scam', TRUE),
(2142, 1071, 'No, it''s safe', FALSE),

-- Q1072 (Scam)
(2143, 1072, 'It''s a scam', TRUE),
(2144, 1072, 'No, it''s safe', FALSE),

-- Q1073 (Scam)
(2145, 1073, 'It''s a scam', TRUE),
(2146, 1073, 'No, it''s safe', FALSE),

-- Q1074 (Scam)
(2147, 1074, 'It''s a scam', TRUE),
(2148, 1074, 'No, it''s safe', FALSE),

-- Q1075 (Scam)
(2149, 1075, 'It''s a scam', TRUE),
(2150, 1075, 'No, it''s safe', FALSE),

-- Q1076 (Safe / Legitimate)
(2151, 1076, 'It''s a scam', FALSE),
(2152, 1076, 'No, it''s safe', TRUE),

-- Q1077 (Safe / Legitimate)
(2153, 1077, 'It''s a scam', FALSE),
(2154, 1077, 'No, it''s safe', TRUE),

-- Q1078 (Safe / Legitimate)
(2155, 1078, 'It''s a scam', FALSE),
(2156, 1078, 'No, it''s safe', TRUE),

-- Q1079 (Safe / Legitimate)
(2157, 1079, 'It''s a scam', FALSE),
(2158, 1079, 'No, it''s safe', TRUE),

-- Q1080 (Safe / Legitimate)
(2159, 1080, 'It''s a scam', FALSE),
(2160, 1080, 'No, it''s safe', TRUE);

-- ==========================================
-- 1. 插入 20 条 Suspicious Links 的测试场景 (使用 1081-1100 作为起始 ID)
-- ==========================================
INSERT INTO quiz_questions (id, category_id, scenario_text, explanation) VALUES
-- 诈骗场景 (15个)
(1081, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'You receive an SMS: "J&T Express: Your parcel is held due to RM1.50 unpaid fee. Pay here: jt-tracking-my.com/pay"', 
 'This is a Smishing (SMS Phishing) scam. Scammers use fake courier domains to steal your credit card details over tiny "fees". Official couriers rarely ask for online payment via SMS.'),

(1082, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'A WhatsApp message forwards a link: "Dear citizen, claim your RM100 eMadani credit here: mysejahtera-claim.info"', 
 'Government initiatives are never claimed via random WhatsApp links using ".info" domains. They must be claimed directly within official e-wallet applications.'),

(1083, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'You get an SMS alert: "CIMB Alert: Suspicious login detected. Secure your account now at cimbclicks-secure.net"', 
 'Look closely at the URL. Banks use their exact official domains (e.g., cimbclicks.com.my). Fake domains like "cimbclicks-secure.net" are phishing sites designed to steal your login credentials.'),

(1084, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'A friend messages you on Facebook Messenger: "Omg is this you in this video?? http://bit.ly/fb-video-892"', 
 'Your friend''s account is hacked. Scammers use URL shorteners (like bit.ly) to hide malicious links that will download malware or direct you to a fake Facebook login page to steal your password.'),

(1085, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'You receive a WhatsApp message from an unknown number: "Hello, here is my wedding invitation!" along with a clickable file named "InvitationCard.apk".', 
 'This is highly dangerous. An ".apk" file is an Android application, not a picture or document. Clicking and installing it allows hackers to read your SMS OTPs and empty your bank account.'),

(1086, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'You see a Facebook ad for "Cheap Home Cleaning RM50". You WhatsApp them, and they send a link to download their "Booking App" outside of the Google Play Store.', 
 'This is a Malware App Scam. The fake app is designed to capture your banking username and password when you try to pay the "deposit". Always download apps from official stores.'),

(1087, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'An email says: "Netflix: Payment declined. Update billing at netflix.update-account.com".', 
 'This is a subdomain trick. The actual domain here is "update-account.com", not "netflix.com". It is a phishing site designed to steal your credit card information.'),

(1088, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'You receive an SMS: "PDRM: RM50 saman for your car. Pay within 24hrs at pdrm-saman-my.org to avoid court action." You do not own a car.', 
 'Scammers create artificial urgency ("avoid court"). Official traffic summons should be checked and paid through verified government portals like MyEG, never through random SMS links.'),

(1089, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'A Telegram message offers you a part-time job: "Earn RM300/day liking Shopee products. Register your profile here: shopee-task-earn.vip"', 
 'This is a Task Scam. E-commerce platforms do not hire people to "like" items via VIP websites. The link will take your personal info and trick you into depositing your own money later.'),

(1090, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'An email arrives from "LHDN" stating you overpaid your income tax. It provides a link to log into your bank to process an RM850 refund.', 
 'Tax authorities (LHDN) do not send refund links via email requiring you to log into your bank. Refunds are processed automatically to the bank account registered in your tax file.'),

(1091, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'You get an SMS: "Maxis: Your 5000 points are expiring today! Redeem a free iPhone 15 at maxis-rewards-claim.com by paying RM5 for shipping."', 
 'This is a loyalty point phishing scam. The link is fake, and the RM5 shipping fee is just an excuse to steal your credit card numbers.'),

(1092, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'You are selling a bag on Carousell. The "buyer" messages: "I already paid, but the system has an error. Click this link to accept my payment: carousell-pay.me/refund"', 
 'Buyers never need to send sellers links to receive money. This link leads to a fake banking login page to steal the seller''s credentials.'),

(1093, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'A random foreign number on WhatsApp strikes up a friendly conversation. A week later, they send a link: "Check out this crypto trading site I use: eth-trading-node.co, it makes me so much money."', 
 'This is a Pig-Butchering (Love/Investment) Scam. The "trading site" is completely controlled by the scammers. Any money you deposit will appear to grow, but you will never be able to withdraw it.'),

(1094, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'An SMS warns: "Your iCloud storage is full. Your photos will be deleted in 24 hours. Upgrade for free at apple-storage-secure.com"', 
 'Scammers use the threat of losing precious data (photos) to make you panic and click the fake Apple login link without thinking.'),

(1095, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'A WhatsApp message claims: "TNG eWallet: Account suspended due to unusual activity. Verify your identity at tng-verify-my.com to reactivate."', 
 'Official e-wallets do not send account suspension notices with links via WhatsApp. You should close the message and open your TNG app directly to check your account status.'),

-- 合法/安全场景 (5个 - 锻炼用户的辨别能力)
(1096, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'You forgot your Maybank2u password and request a reset. Five seconds later, you receive an email with a reset link starting with "https://www.maybank2u.com.my/"', 
 'This is safe. You initiated the action, you expected the email immediately, and the URL exactly matches the official, secure bank domain.'),

(1097, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'You purchase a flight ticket on AirAsia. The confirmation email includes a link "https://www.airasia.com/manage-booking" to view your itinerary.', 
 'This is safe. It is a standard transactional email related to a recent purchase you made, and the link points to the official airline domain.'),

(1098, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'Your university lecturer posts an announcement in the official Monash student portal containing a link to "https://drive.google.com/..." to download lecture slides.', 
 'This is safe. The link was shared on an authenticated, trusted platform (the student portal) by a known person, using a legitimate file-sharing service.'),

(1099, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'You open your official EPF (KWSP) app, navigate to the Help section, and click a link that opens an FAQ page on "https://www.kwsp.gov.my/"', 
 'This is safe. You navigated from inside the secure application, and the link directs you to an official government domain (.gov.my).'),

(1100, (SELECT id FROM scam_categories WHERE name = 'Suspicious Links' LIMIT 1), 
 'A major national news website publishes an article advising citizens to check suspicious bank accounts. They include a link to the official police portal: "https://semakmule.rmp.gov.my/"', 
 'This is safe. The domain ".gov.my" is strictly controlled and reserved for Malaysian government entities, making this an official and safe verification tool.');


-- ==========================================
-- 2. 插入对应的选项 (每个问题2个选项，ID 2161-2200)
-- ==========================================
INSERT INTO quiz_options (id, question_id, option_text, is_correct) VALUES
-- Q1081 (Scam)
(2161, 1081, 'It''s a scam', TRUE),
(2162, 1081, 'No, it''s safe', FALSE),

-- Q1082 (Scam)
(2163, 1082, 'It''s a scam', TRUE),
(2164, 1082, 'No, it''s safe', FALSE),

-- Q1083 (Scam)
(2165, 1083, 'It''s a scam', TRUE),
(2166, 1083, 'No, it''s safe', FALSE),

-- Q1084 (Scam)
(2167, 1084, 'It''s a scam', TRUE),
(2168, 1084, 'No, it''s safe', FALSE),

-- Q1085 (Scam)
(2169, 1085, 'It''s a scam', TRUE),
(2170, 1085, 'No, it''s safe', FALSE),

-- Q1086 (Scam)
(2171, 1086, 'It''s a scam', TRUE),
(2172, 1086, 'No, it''s safe', FALSE),

-- Q1087 (Scam)
(2173, 1087, 'It''s a scam', TRUE),
(2174, 1087, 'No, it''s safe', FALSE),

-- Q1088 (Scam)
(2175, 1088, 'It''s a scam', TRUE),
(2176, 1088, 'No, it''s safe', FALSE),

-- Q1089 (Scam)
(2177, 1089, 'It''s a scam', TRUE),
(2178, 1089, 'No, it''s safe', FALSE),

-- Q1090 (Scam)
(2179, 1090, 'It''s a scam', TRUE),
(2180, 1090, 'No, it''s safe', FALSE),

-- Q1091 (Scam)
(2181, 1091, 'It''s a scam', TRUE),
(2182, 1091, 'No, it''s safe', FALSE),

-- Q1092 (Scam)
(2183, 1092, 'It''s a scam', TRUE),
(2184, 1092, 'No, it''s safe', FALSE),

-- Q1093 (Scam)
(2185, 1093, 'It''s a scam', TRUE),
(2186, 1093, 'No, it''s safe', FALSE),

-- Q1094 (Scam)
(2187, 1094, 'It''s a scam', TRUE),
(2188, 1094, 'No, it''s safe', FALSE),

-- Q1095 (Scam)
(2189, 1095, 'It''s a scam', TRUE),
(2190, 1095, 'No, it''s safe', FALSE),

-- Q1096 (Safe / Legitimate)
(2191, 1096, 'It''s a scam', FALSE),
(2192, 1096, 'No, it''s safe', TRUE),

-- Q1097 (Safe / Legitimate)
(2193, 1097, 'It''s a scam', FALSE),
(2194, 1097, 'No, it''s safe', TRUE),

-- Q1098 (Safe / Legitimate)
(2195, 1098, 'It''s a scam', FALSE),
(2196, 1098, 'No, it''s safe', TRUE),

-- Q1099 (Safe / Legitimate)
(2197, 1099, 'It''s a scam', FALSE),
(2198, 1099, 'No, it''s safe', TRUE),

-- Q1100 (Safe / Legitimate)
(2199, 1100, 'It''s a scam', FALSE),
(2200, 1100, 'No, it''s safe', TRUE);


-- ==========================================
-- 3. (非常重要) 同步 PostgreSQL 的自增序列
-- ==========================================
SELECT setval(pg_get_serial_sequence('quiz_questions', 'id'), coalesce(max(id),0) + 1, false) FROM quiz_questions;
SELECT setval(pg_get_serial_sequence('quiz_options', 'id'), coalesce(max(id),0) + 1, false) FROM quiz_options;

