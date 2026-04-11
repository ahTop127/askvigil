import { memo } from "react";
import { motion } from "motion/react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@components/ui/accordion";

/**
 * Marketing FAQ accordion.
 */
export const FAQSection = memo(function FAQSection() {
  return (
    <section className="py-16 bg-white">
      <div className="max-w-4xl mx-auto px-[41px] py-[0px]">
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="text-center mb-12"
        >
          <h2 className="font-bold text-gray-900 mb-4 text-[48px]">
            Frequently Asked Questions
          </h2>
          <p className="text-lg text-gray-600">
            Get answers to common questions
          </p>
        </motion.div>

        <Accordion type="single" collapsible className="space-y-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <AccordionItem
              value="item-1"
              className="bg-gray-50 rounded-xl px-6 border border-gray-200 hover:border-[#54A388] transition-colors"
            >
              <AccordionTrigger className="hover:no-underline">
                How does AskVigil check scam messages?
              </AccordionTrigger>
              <AccordionContent className="text-gray-600">
                AskVigil uses advanced pattern recognition to analyze suspicious
                messages, links, images, and QR codes. Our system checks for
                common scam indicators like urgent language, suspicious URLs,
                and phishing patterns to give you an instant risk assessment.
              </AccordionContent>
            </AccordionItem>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <AccordionItem
              value="item-2"
              className="bg-gray-50 rounded-xl px-6 border border-gray-200 hover:border-[#54A388] transition-colors"
            >
              <AccordionTrigger className="hover:no-underline">
                Is my data safe when I submit content for checking?
              </AccordionTrigger>
              <AccordionContent className="text-gray-600">
                Yes, your privacy is our priority. All submitted content is
                processed securely and not stored permanently. We only analyze
                the content to provide you with a risk assessment and do not
                share your data with third parties.
              </AccordionContent>
            </AccordionItem>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <AccordionItem
              value="item-3"
              className="bg-gray-50 rounded-xl px-6 border border-gray-200 hover:border-[#54A388] transition-colors"
            >
              <AccordionTrigger className="hover:no-underline">
                What should I do if I&apos;ve already fallen for a scam?
              </AccordionTrigger>
              <AccordionContent className="text-gray-600">
                Visit our Guidance section for step-by-step instructions on what
                to do after being scammed. Depending on the scam type, we
                provide specific guidance on contacting authorities, securing
                your accounts, and preventing further damage.
              </AccordionContent>
            </AccordionItem>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <AccordionItem
              value="item-4"
              className="bg-gray-50 rounded-xl px-6 border border-gray-200 hover:border-[#54A388] transition-colors"
            >
              <AccordionTrigger className="hover:no-underline">
                Is AskVigil free to use?
              </AccordionTrigger>
              <AccordionContent className="text-gray-600">
                Yes! AskVigil is completely free to use. Our mission is to
                protect young Malaysians from online scams by providing
                accessible, easy-to-use scam detection and educational
                resources.
              </AccordionContent>
            </AccordionItem>
          </motion.div>
        </Accordion>
      </div>
    </section>
  );
});
