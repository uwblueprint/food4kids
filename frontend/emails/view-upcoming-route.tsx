import { Button, Heading, Section,Text } from "@react-email/components";

import F4KEmailLayout from "./components/F4KEmailLayout";

export default function ViewUpcomingRouteEmail() {
    return (
        <F4KEmailLayout previewText="View Your Upcoming F4K Route">

        <Section className="px-[34px] pt-[10px] pb-[17px]">
            <Heading className="text-[32px] font-nunito font-bold text-grey-500 mb-[24px]">
                View your upcoming route
            </Heading>
            
            <Text className="text-[16px] text-grey-500 m-0 mb-[24px]">
                Hi Driver_Name_To_Replace,
            </Text>
            <Text className="text-[16px] text-grey-500 m-0 mb-[24px]">
                This is a reminder that you have an upcoming delivery route scheduled:
            </Text>
            <ul className="m-0 mb-[24px] pl-[24px] font-nunito-sans text-[16px] leading-[24px] text-grey-500">
                <li className="">
                    <strong>Date:</strong> Date_To_Replace
                </li>
                <li className="">
                    <strong>Start Time:</strong> Time_To_Replace
                </li>
                <li className="">
                    <strong>Route Duration:</strong> Route_Duration_To_Replace
                </li>
            </ul>
            <Text className="text-[16px] text-grey-500">
                You can review all stops, delivery instructions, and contact details using the button below.
            </Text>

            <Section className="text-center mt-[32px] mb-[32px]">
                <Button 
                // REPLACE THIS WITH ACTUAL URL (unless we want to Rick Roll recipients...)
                href="Upcoming_Route_URL" 
                className="rounded-full border border-solid border-blue-400 bg-blue-300 px-[56px] py-[11px] font-nunito text-grey-100 text-[16px] tracking-wide"
                >
                    View Route
                </Button>
            </Section>

            <Text className="text-[16px] text-grey-500">
                Thank you for delivering with Food4Kids!
            </Text>
        </Section>
        
        </F4KEmailLayout>
    );
}
