from __future__ import annotations


class ATSValidator:


    @staticmethod
    async def validate(
        provider,
        board,
    ):

        jobs = await provider.client.get_jobs(
            board.board
        )


        return {

            "company": board.company,

            "ats": board.ats,

            "board": board.board,

            "valid": len(jobs) > 0,

            "job_count": len(jobs),

        }