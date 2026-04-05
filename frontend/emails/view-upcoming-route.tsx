    import { Text, Button, Heading, Img, Section } from "@react-email/components";
    import * as React from "react";
    import F4KEmailLayout from "./components/Layout";

    export default function ViewUpcomingRouteEmail() {
    return (
        <F4KEmailLayout previewText="View Your Upcoming F4K Route">

        <Heading className="text-2xl font-nunito font-bold text-grey-500 mt-[32px] mb-[38px] text-center">
            View your upcoming route
        </Heading>
        
        <Text className="text-[16px] leading-[24px] text-grey-500 m-0 mb-[32px]">
            Hi {"{{Driver Name}}"},
        </Text>
        <Text className="text-[14px] text-grey-500 m-0 mb-[32px]">
            This is a reminder that you have an upcoming delivery route scheduled:
        </Text>
        <ul className="m-0 mb-[32px] pl-[24px] font-nunito-sans text-[16px] text-grey-500">

        <li className="mb-[8px]">
            <strong>Date: [DATE]</strong>
        </li>
        <li className="mb-[8px]">
            <strong>Start Time: [TIME]</strong>
        </li>
        <li className="mb-[8px]">
            <strong>Route Duration: [KMS]</strong>
        </li>
        
        </ul>
        <Text className="text-[14px] text-grey-500 m-0 mb-[8px]">
            You can review all stops, instructions, and contact details using the button below.
        </Text>


        <Section className="text-center mt-[36px] mb-[36px]">
            <Button 
            // REPLACE THIS WITH ACTUAL URL (unless we want to Rick Roll recipients...)
            href="https://www.youtube.com/watch?v=dQw4w9WgXcQ" 
            className="rounded-md bg-blue-300 px-[32px] py-[14px] font-nunito font-bold text-grey-100 text-[16px] tracking-wide"
            >
            View Route
            </Button>
        </Section>

        <Text className="text-[14px] text-grey-500 m-0 mb-[16px]">
            Thank you for delivering with Food4Kids!
        </Text>
        
        </F4KEmailLayout>
    );
    }